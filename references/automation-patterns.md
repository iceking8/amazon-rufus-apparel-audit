# 自动化代码模式

可执行代码片段。配合 [browser-capture.md](browser-capture.md) 的护栏使用。代码取自 amazon-rufus-qa skill 的实战经验,改掉了凭据 stdin、硬编码路径、绝对成功率断言等不安全做法。

## 目录

1. 浏览器连接 + 单 async 块原则
2. ASIN 优先导航
3. Rufus 元素探针(JS)
4. React-safe 输入 + 提交
5. 答案提取与稳定判定
6. 批量循环骨架
7. 失败处理映射
8. 凭据获取(只走环境变量,绝无 stdin)

---

## 1. 浏览器连接 + 单 async 块原则

CDP 可用时,**每个原子动作放进单个浏览器侧 async 块**——这能保持 DOM 状态在页面内,避免跨调用的 stale reference。

伪代码:

```text
connect to existing browser
verify active tab is target Amazon page
run one browser-side async function:
  locate Rufus
  set input
  submit
  wait for answer
  return structured result
save row in Python side
```

如果用 browser-harness,把它的 `js()` 当浏览器侧函数 runner;Playwright 用 `page.evaluate()`;裸 CDP 用 `Runtime.evaluate`。

**避免**把一道题的逻辑拆到很多无关调用里,除非自动化库稳定管理 element handle。

---

## 2. ASIN 优先导航

ASIN 任务**必须**先到产品页:

```python
def navigate_to_asin(ws, asin, marketplace="com"):
    url = f"https://www.amazon.{marketplace}/dp/{asin}"
    cdp_send(ws, "Page.navigate", {"url": url})
    wait_for_load(ws, timeout=10)
    
    # 验证 ASIN 一致
    actual_asin = cdp_eval(ws, """
        document.querySelector('input[name="ASIN"]')?.value
        || (document.URL.match(/\\/dp\\/([A-Z0-9]+)/) || [])[1]
    """)
    if actual_asin != asin:
        return {"status": "blocked", "reason": "page_mismatch"}
    return {"status": "ok"}
```

**绝不**用 `/s?k=...` 搜索页代替 ASIN 级抓取——除非用户明确要求做品类研究。

---

## 3. Rufus 元素探针

```javascript
// 在浏览器里跑这一段验证 Rufus 当前页可用
(function probeRufus() {
    const openButton = document.querySelector('.nav-rufus-disco-text, .nav-rufus-disco');
    const panel = document.querySelector('#nav-flyout-rufus');
    const input = document.querySelector('#rufus-text-area, textarea[aria-label*="Rufus"]');
    const submit = document.querySelector('#rufus-submit-button, [data-testid="rufus-submit"]');
    
    return {
        openButton: !!openButton,
        panel: !!panel,
        panelVisible: panel && getComputedStyle(panel).visibility === 'visible',
        input: !!input,
        submit: !!submit,
        // 验证 submit 跟 input 在同一 form
        sameForm: submit && input && submit.closest('form') === input.closest('form')
    };
})();
```

任何一项 false → 标 `selector_verification_failed`,停掉这个 ASIN,继续下一个。

---

## 4. React-safe 输入 + 提交(核心代码)

Rufus textarea 是 React 受控组件,`textarea.value = "..."` 不会更新 React state。**必须**用 native setter + dispatch input/change:

```javascript
function setReactText(el, text) {
    const proto = el instanceof HTMLTextAreaElement
        ? HTMLTextAreaElement.prototype
        : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
    if (!setter) throw new Error('native value setter not found');
    setter.call(el, text);
    el.dispatchEvent(new InputEvent('input', { 
        bubbles: true, inputType: 'insertText', data: text 
    }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
}

function dispatchClick(el) {
    for (const type of ['pointerdown', 'mousedown', 'mouseup', 'click']) {
        el.dispatchEvent(new MouseEvent(type, {
            bubbles: true, cancelable: true, view: window
        }));
    }
}

async function askOneRufus(question, opts = {}) {
    const opener = document.querySelector('.nav-rufus-disco-text, .nav-rufus-disco');
    if (!opener) return { ok: false, reason: 'no_opener' };
    opener.click();
    await new Promise(r => setTimeout(r, 1500));
    
    const panel = document.getElementById('nav-flyout-rufus');
    if (!panel) return { ok: false, reason: 'no_panel' };
    
    const input = document.getElementById('rufus-text-area');
    const submit = document.querySelector('#rufus-submit-button, [data-testid="rufus-submit"]');
    if (!input || !submit) return { ok: false, reason: 'no_input_or_submit' };
    
    // 验证 input 和 submit 在同 form
    if (input.closest('form') !== submit.closest('form')) {
        return { ok: false, reason: 'form_mismatch' };
    }
    
    input.focus();
    setReactText(input, question);
    await new Promise(r => setTimeout(r, 300));
    dispatchClick(submit);
    
    // 验证 submit 被 acknowledge:有新的 user turn 出现
    const acked = await waitFor(
        () => panel.innerText.includes(question.slice(0, 30)),
        { timeoutMs: 5000, checkMs: 250 }
    );
    if (!acked) return { ok: false, reason: 'submit_not_acknowledged' };
    
    // 等答案稳定
    const answer = await waitForStableAnswer(panel, opts);
    if (!answer.ok) return { ok: false, reason: answer.reason };
    
    return { ok: true, ...answer };
}

function waitFor(predicate, { timeoutMs, checkMs }) {
    return new Promise(resolve => {
        const start = Date.now();
        const tick = () => {
            if (predicate()) return resolve(true);
            if (Date.now() - start > timeoutMs) return resolve(false);
            setTimeout(tick, checkMs);
        };
        tick();
    });
}
```

**关键点**:

- 用 `pointerdown`/`mousedown`/`mouseup`/`click` 的完整序列,光 `click()` 在某些 React 版本下不触发
- 提交后必须**验证**新的 user turn 出现,而不是相信 click 没报错就算成功

---

## 5. 答案提取 + 稳定判定

```javascript
async function waitForStableAnswer(panel, opts = {}) {
    const maxWaitMs = opts.maxWaitMs || 60_000;     // 长答案放到 90s
    const stabilityCheckMs = opts.stabilityCheckMs || 1500;
    const start = Date.now();
    
    let lastLen = -1;
    let stableHits = 0;
    
    while (Date.now() - start < maxWaitMs) {
        await new Promise(r => setTimeout(r, stabilityCheckMs));
        
        // 找最新 assistant turn
        const turns = panel.querySelectorAll('[role="article"], .assistant-turn, [data-testid*="rufus-message"]');
        const latestAssistant = turns.length 
            ? turns[turns.length - 1] 
            : null;
        
        const text = latestAssistant 
            ? latestAssistant.innerText 
            : panel.innerText;  // fallback
        
        const isThinking = text.includes('Thinking') 
            || text.includes('generating') 
            || panel.querySelector('[aria-label*="thinking" i]');
        const hasResume = !!panel.querySelector('[aria-label*="Resume" i], button:contains("Resume response")');
        
        if (isThinking || hasResume) {
            stableHits = 0;
            continue;
        }
        
        if (text.length === lastLen && text.length > 50) {
            stableHits++;
            if (stableHits >= 2) {
                // 稳定
                const followups = Array.from(
                    panel.querySelectorAll('button[data-testid*="suggestion"], button.followup')
                ).map(b => b.innerText.trim()).filter(Boolean);
                
                return {
                    ok: true,
                    answer: text,
                    answerLength: text.length,
                    followups,
                    selectorStrategy: latestAssistant ? 'latest_assistant_turn' : 'panel_text_fallback'
                };
            }
        } else {
            stableHits = 0;
            lastLen = text.length;
        }
    }
    
    return { ok: false, reason: 'answer_stabilization_timeout' };
}
```

**注意**:

- `latestAssistant` 找不到时降级到 `panel.innerText`,但要标 `panel_text_fallback`
- `stableHits >= 2` 表示连续两次长度不变才算稳定
- `text.length > 50` 排除空 panel

---

## 6. 批量循环骨架(Python 侧)

```python
import json
import time
from datetime import datetime
from pathlib import Path

class RufusCapture:
    def __init__(self, cdp_ws, output_dir):
        self.ws = cdp_ws
        self.out = Path(output_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.rows = []
    
    def verify_login(self):
        result = cdp_eval(self.ws, """
            document.querySelector('#nav-link-accountList-nav-line-1')?.innerText || ''
        """)
        if 'Hello' not in result and 'Hi,' not in result:
            return {'logged_in': False, 'evidence': result}
        return {'logged_in': True, 'name_hint': result}
    
    def check_mobile_required(self):
        return cdp_eval(self.ws, """
            (function() {
                const txt = document.body.innerText.toLowerCase();
                return txt.includes('add a mobile number') 
                    || txt.includes('add mobile number')
                    || !!document.querySelector('input[name*="phone" i]');
            })()
        """)
    
    def capture_one(self, asin, planned_question):
        # 1. 导航
        nav = navigate_to_asin(self.ws, asin)
        if nav['status'] != 'ok':
            return self._fail_row(asin, planned_question, 'page_mismatch')
        
        # 2. 探针
        probe = cdp_eval(self.ws, "(...probe code...)")
        if not all(probe.values()):
            return self._fail_row(asin, planned_question, 'selector_verification_failed')
        
        # 3. 提问
        result = cdp_eval_async(self.ws, f"""
            askOneRufus({json.dumps(planned_question['question_text'])}, {{maxWaitMs: 60000}})
        """)
        
        if not result['ok']:
            return self._fail_row(asin, planned_question, result.get('reason', 'unknown'))
        
        # 4. 入库
        row = {
            'capture_id': f"{planned_question['planned_question_id']}-CAP",
            'capture_date': datetime.now().isoformat(),
            'asin': asin,
            'planned_question_id': planned_question['planned_question_id'],
            'question_origin': planned_question['question_origin'],
            'profile_signal': planned_question.get('profile_signal'),
            'capture_status': 'answered',
            'raw_question': planned_question['question_text'],
            'normalized_question': normalize_q(planned_question['question_text']),
            'raw_answer': result['answer'],
            'answer_length_chars': result['answerLength'],
            'follow_up_prompts': result['followups'],
            'selector_strategy': result['selectorStrategy'],
            'submit_attempt_count': 1,
            'submit_method': 'click_dispatch',
        }
        self.rows.append(row)
        return row
    
    def _fail_row(self, asin, planned, reason):
        row = {
            'capture_id': f"{planned['planned_question_id']}-CAP",
            'capture_date': datetime.now().isoformat(),
            'asin': asin,
            'planned_question_id': planned['planned_question_id'],
            'capture_status': 'question_only' if reason in {'submit_not_acknowledged', 'answer_stabilization_timeout'} else 'blocked',
            'failure_reason': reason,
            'raw_question': planned['question_text'],
        }
        self.rows.append(row)
        return row
    
    def run_asin(self, asin, plan):
        login = self.verify_login()
        if not login['logged_in']:
            self.save_blocker('amazon_buyer_login_required')
            return False
        
        if self.check_mobile_required():
            self.save_blocker('mobile_number_verification_required')
            return False
        
        for q in plan:
            self.capture_one(asin, q)
            time.sleep(2)  # 不是为了绕风控,是为了 UI 不过载
            
            # 关闭 Rufus 面板减少上下文污染(qa 思路保留)
            if len(self.rows) % 5 == 0:
                cdp_eval(self.ws, """
                    const close = document.querySelector('[aria-label*="Close" i]');
                    if (close) close.click();
                """)
                time.sleep(1)
        
        return True
    
    def save_blocker(self, reason):
        # 通过 chat 通道告诉用户(此处由调用方实现)
        # 不要 print 凭据 / 手机号 / 验证码
        with open(self.out / 'blocker.json', 'w') as f:
            json.dump({'reason': reason, 'time': datetime.now().isoformat()}, f)
    
    def save_final(self):
        with open(self.out / 'capture_baseline.csv', 'w') as f:
            # 写表头 + 每行
            ...
```

---

## 7. 失败处理映射表

| 现象 | capture_status | failure_reason |
|---|---|---|
| Rufus panel 不出现 | blocked | rufus_not_visible |
| 没登录 | blocked | amazon_buyer_login_required |
| 手机验证 | blocked | mobile_number_verification_required |
| submit click 没产生 user turn | question_only | submit_not_acknowledged |
| 提交后 5 秒没答 | question_only | first_answer_timeout |
| 答案不稳定超时 | question_only | answer_stabilization_timeout |
| 多题卡 thinking | blocked | thinking_timeout |
| 连续 3 次 check 无变化 | blocked | no_state_progress |
| 探针失败 | blocked | selector_verification_failed |
| 页面 ASIN 不对 | blocked | page_mismatch |

**永远不要**因为某行失败就跳过它,失败行也要入库,带原因,这才能在 Capture Health 里诚实说明。

---

## 8. 凭据获取(死规矩:绝无 stdin)

```python
import os
from pathlib import Path

def get_amazon_credentials():
    """凭据只能从环境变量或 user-provided secret file 拿。
    任何 input() / sys.stdin.readline() 都不允许。
    """
    email = os.environ.get('AMAZON_BUYER_EMAIL')
    password = os.environ.get('AMAZON_BUYER_PASSWORD')
    
    if not email or not password:
        # 不阻塞,也不 input() — 直接抛出,让上层通过 chat 通道问用户
        raise CredentialsNotProvided(
            "凭据未配置。请通过环境变量 AMAZON_BUYER_EMAIL / AMAZON_BUYER_PASSWORD 提供,"
            "或在 secrets 文件中配置。绝不通过 stdin 收集凭据。"
        )
    
    return email, password


def get_otp_or_phone(challenge_type):
    """OTP / 手机号 / 短信码同理:走环境变量或 secret 通道。"""
    env_keys = {
        'otp': 'AMAZON_BUYER_OTP_SECRET',
        'phone': 'AMAZON_BUYER_PHONE',
        'sms_code': 'AMAZON_BUYER_SMS_CODE',  # 临时,用完清掉
    }
    val = os.environ.get(env_keys[challenge_type])
    if not val:
        raise CredentialsNotProvided(
            f"{challenge_type} 未配置。请通过环境变量提供,或让 agent 通过 chat 问用户。"
        )
    return val


class CredentialsNotProvided(Exception):
    pass
```

**为什么严禁 stdin**:

- 后台 agent 跑批时 stdin 被关闭,`input()` 直接抛 EOFError 整个 run 崩
- stdin 输入会被 ps/strace/log 捕获,密码泄露风险
- 多 ASIN 任务里中途要 OTP,每次都阻塞等用户输入,跑批就废了

**正确流程**:

1. 任务开始前,环境变量已设置(用户通过 secrets 文件 / shell export / agent 框架的 secret 通道注入)
2. 缺凭据 → 抛 `CredentialsNotProvided`,上层捕获 → 通过 chat 通道告诉用户怎么配
3. 配完用户重启任务(or hot reload),不阻塞当前进程
