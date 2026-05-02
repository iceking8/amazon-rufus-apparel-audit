#!/usr/bin/env python3
"""
单 ASIN Rufus 抓取主程序

实现 references/browser-capture.md 描述的状态机:
  ready → login_check → listing_snapshot → product_profile
       → question_plan → submit_one_question → wait_thinking
       → wait_stable → capture_answer → loop → final_save → close_browser

跟原 qa skill 的 batch_ask 区别:
1. 状态机驱动,失败行不丢
2. 一次只问一题,严格 sequential submission rule
3. 答案稳定判定不只看 length > 200,而是看 thinking 消失 + length 不变
4. 不靠"关闭面板重置限流"作为成功率保证 — 关面板是为了减少上下文污染
5. CSV 输出 30+ 字段,带完整失败原因和 verification 状态

环境变量:
  CHROME_REMOTE_PORT(默认 9222)

用法:
  python3 scripts/capture_rufus.py \
      --asin B0XXXXXXX \
      --role own \
      --depth 20 \
      --marketplace com \
      --output-dir out/

  # 多 ASIN(批量,逗号分隔):
  python3 scripts/capture_rufus.py \
      --asins B0AAA,B0BBB,B0CCC \
      --roles own,competitor_1,competitor_2 \
      --depth 20

  # 跳过 profile/plan(用已有的 plan):
  python3 scripts/capture_rufus.py \
      --asin B0XXXX --role own \
      --plan-file out/question_plan.csv

依赖:
  pip3 install websockets --break-system-packages
"""
import argparse
import asyncio
import csv
import json
import os
import re
import sys
import time
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import websockets
except ImportError:
    print("✗ pip3 install websockets --break-system-packages")
    sys.exit(1)


CHROME_PORT = int(os.environ.get('CHROME_REMOTE_PORT', '9222'))


@dataclass
class CaptureRow:
    capture_id: str
    capture_date: str
    marketplace: str
    product_role: str
    asin: str
    product_url: str
    persona_label: str = "default"
    login_status: str = "unknown"
    challenge_type: str = "none"
    verification_action: str = "none"
    source_depth: int = 0
    parent_question_id: str = ""
    planned_question_id: str = ""
    question_origin: str = "rufus_starter"
    profile_signal: str = ""
    capture_status: str = "answered"
    failure_reason: str = ""
    raw_question: str = ""
    normalized_question: str = ""
    raw_answer: str = ""
    answer_summary: str = ""
    answer_length_chars: int = 0
    answer_confidence: str = "high"
    answer_type: str = ""
    follow_up_prompts: str = ""
    primary_dimension: str = ""
    sub_category: str = ""
    buyer_concern_cn: str = ""
    competitor_strength: str = ""
    competitor_mentions: str = ""
    price_evidence: str = ""
    review_evidence_summary: str = ""
    concern_scope: str = ""
    recovery_action: str = ""
    submit_attempt_count: int = 0
    submit_method: str = ""
    selector_strategy: str = ""
    notes: str = ""


# ============================================================
# CDP 通信
# ============================================================

class CDPClient:
    def __init__(self, ws):
        self.ws = ws
        self._counter = 0
    
    def _next_id(self):
        self._counter += 1
        return self._counter
    
    async def send(self, method, params=None):
        msg_id = self._next_id()
        await self.ws.send(json.dumps({
            'id': msg_id, 'method': method, 'params': params or {}
        }))
        while True:
            resp = json.loads(await self.ws.recv())
            if resp.get('id') == msg_id:
                if 'error' in resp:
                    raise RuntimeError(f"CDP error: {resp['error']}")
                return resp.get('result', {})
    
    async def eval(self, expression, await_promise=False, timeout_ms=30000):
        result = await self.send('Runtime.evaluate', {
            'expression': expression,
            'returnByValue': True,
            'awaitPromise': await_promise,
            'timeout': timeout_ms,
        })
        r = result.get('result', {})
        if r.get('subtype') == 'error':
            raise RuntimeError(f"JS error: {r.get('description', '')}")
        return r.get('value')


async def get_cdp_ws_url():
    url = f'http://127.0.0.1:{CHROME_PORT}/json/version'
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.loads(r.read())['webSocketDebuggerUrl']


# ============================================================
# 状态机各阶段
# ============================================================

async def state_login_check(cdp: CDPClient):
    name = await cdp.eval(
        "document.querySelector('#nav-link-accountList-nav-line-1')?.innerText || ''"
    )
    if name and ('Hello' in name or 'Hi,' in name):
        return {'logged_in': True, 'evidence': name}
    return {'logged_in': False, 'evidence': name or 'no_header_text'}


async def state_check_mobile_required(cdp: CDPClient):
    return await cdp.eval("""
        (function() {
            const txt = (document.body.innerText || '').toLowerCase();
            return txt.includes('add a mobile number')
                || txt.includes('add mobile number')
                || !!document.querySelector('input[name*="phone" i]:not([type="hidden"])');
        })()
    """)


async def state_navigate_asin(cdp: CDPClient, asin: str, marketplace: str = "com"):
    url = f"https://www.amazon.{marketplace}/dp/{asin}"
    await cdp.send('Page.navigate', {'url': url})
    await asyncio.sleep(3)
    
    # 等到页面有 Rufus 按钮或 product title
    for _ in range(15):
        ready = await cdp.eval("""
            !!document.querySelector('#productTitle, .nav-rufus-disco, .nav-rufus-disco-text')
        """)
        if ready:
            break
        await asyncio.sleep(1)
    
    # 验证 ASIN 一致
    actual = await cdp.eval(f"""
        (function() {{
            const inp = document.querySelector('input[name="ASIN"]');
            if (inp) return inp.value;
            const m = document.URL.match(/\\/dp\\/([A-Z0-9]+)/);
            return m ? m[1] : '';
        }})()
    """)
    
    return {
        'ok': actual == asin,
        'actual_asin': actual,
        'url': url,
    }


async def state_listing_snapshot(cdp: CDPClient):
    """快速读 Listing 关键字段。"""
    return await cdp.eval("""
        (function() {
            const t = (sel) => document.querySelector(sel)?.innerText?.trim() || '';
            const ts = (sel) => Array.from(document.querySelectorAll(sel)).map(e => e.innerText.trim());
            return {
                title: t('#productTitle'),
                brand: t('#bylineInfo'),
                price: t('.a-price .a-offscreen'),
                rating: t('[data-hook="rating-out-of-text"], #acrPopover .a-icon-alt'),
                reviewCount: t('#acrCustomerReviewText'),
                bullets: ts('#feature-bullets li:not(.aok-hidden)').slice(0, 8),
                imageCount: document.querySelectorAll('#altImages li img, #imageBlock img.a-dynamic-image').length,
                hasAplus: !!document.querySelector('#aplus_feature_div, #aplus, #aplusBrandStory_feature_div'),
            };
        })()
    """)


# ============================================================
# Rufus 探针 + 提问
# ============================================================

PROBE_RUFUS_JS = """
(function() {
    const o = document.querySelector('.nav-rufus-disco-text, .nav-rufus-disco');
    const p = document.querySelector('#nav-flyout-rufus');
    const i = document.querySelector('#rufus-text-area, textarea[aria-label*="Rufus" i]');
    const s = document.querySelector('#rufus-submit-button, [data-testid="rufus-submit"]');
    return {
        opener: !!o,
        panel: !!p,
        input: !!i,
        submit: !!s,
        sameForm: !!(s && i && s.closest('form') === i.closest('form'))
    };
})()
"""


ASK_RUFUS_JS_TEMPLATE = r"""
(async function(question) {
    function setReactText(el, text) {
        const proto = el instanceof HTMLTextAreaElement
            ? HTMLTextAreaElement.prototype
            : HTMLInputElement.prototype;
        const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
        setter.call(el, text);
        el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
    }
    function dispatchClick(el) {
        for (const t of ['pointerdown','mousedown','mouseup','click']) {
            el.dispatchEvent(new MouseEvent(t, { bubbles: true, cancelable: true, view: window }));
        }
    }
    
    const opener = document.querySelector('.nav-rufus-disco-text, .nav-rufus-disco');
    if (!opener) return { ok: false, reason: 'rufus_not_visible' };
    opener.click();
    await new Promise(r => setTimeout(r, 1500));
    
    const panel = document.getElementById('nav-flyout-rufus');
    if (!panel) return { ok: false, reason: 'rufus_not_visible' };
    
    const input = document.getElementById('rufus-text-area');
    const submit = document.querySelector('#rufus-submit-button, [data-testid="rufus-submit"]');
    if (!input || !submit) return { ok: false, reason: 'selector_verification_failed' };
    if (input.closest('form') !== submit.closest('form')) {
        return { ok: false, reason: 'selector_verification_failed' };
    }
    
    input.focus();
    setReactText(input, question);
    await new Promise(r => setTimeout(r, 300));
    dispatchClick(submit);
    
    // 等 user turn 出现
    let acked = false;
    const ackStart = Date.now();
    while (Date.now() - ackStart < 6000) {
        await new Promise(r => setTimeout(r, 250));
        if (panel.innerText.includes(question.slice(0, Math.min(40, question.length)))) {
            acked = true;
            break;
        }
    }
    if (!acked) return { ok: false, reason: 'submit_not_acknowledged' };
    
    // 等答案稳定
    let lastLen = -1;
    let stableHits = 0;
    const start = Date.now();
    const maxMs = 90000;  // 90s,长答案兜底
    
    while (Date.now() - start < maxMs) {
        await new Promise(r => setTimeout(r, 1500));
        
        const txt = panel.innerText || '';
        const isThinking = txt.includes('Thinking') 
            || txt.includes('generating')
            || /generat\\w*…/i.test(txt);
        const hasResume = !!panel.querySelector('[aria-label*="Resume" i]');
        
        if (isThinking || hasResume) {
            stableHits = 0;
            continue;
        }
        
        if (txt.length === lastLen && txt.length > 100) {
            stableHits++;
            if (stableHits >= 2) {
                // 提取 follow-up
                const followups = Array.from(panel.querySelectorAll(
                    'button[data-testid*="suggestion" i], button[data-testid*="follow" i]'
                )).map(b => b.innerText.trim()).filter(Boolean);
                
                // 尝试只抓最新 assistant turn
                const turns = panel.querySelectorAll('[role="article"], [data-testid*="rufus-message" i]');
                let scopedAnswer = txt;
                let strategy = 'panel_text_fallback';
                if (turns.length) {
                    scopedAnswer = turns[turns.length - 1].innerText;
                    strategy = 'latest_assistant_turn';
                }
                
                return {
                    ok: true,
                    answer: scopedAnswer,
                    panelText: txt,
                    answerLength: scopedAnswer.length,
                    followups: followups,
                    selectorStrategy: strategy,
                };
            }
        } else {
            stableHits = 0;
            lastLen = txt.length;
        }
    }
    
    return { ok: false, reason: 'answer_stabilization_timeout' };
})(__QUESTION__)
"""


async def ask_rufus(cdp: CDPClient, question: str):
    js = ASK_RUFUS_JS_TEMPLATE.replace('__QUESTION__', json.dumps(question))
    return await cdp.eval(js, await_promise=True, timeout_ms=120000)


async def close_rufus_panel(cdp: CDPClient):
    """关闭 Rufus 面板,减少下一题的上下文污染。
    
    注意:这不是限流绕过,只是为了避免 Rufus 把上一题答案当成本题上下文。
    """
    await cdp.eval("""
        const close = document.querySelector('[aria-label*="Close" i][aria-label*="rufus" i]')
            || document.querySelector('#nav-flyout-rufus button[aria-label*="Close" i]');
        if (close) close.click();
    """)
    await asyncio.sleep(1)


# ============================================================
# Question plan 处理
# ============================================================

def normalize_question(q):
    return re.sub(r'\s+', ' ', q.lower().strip(' ?.,!"\''))


def load_plan_csv(path):
    plan = []
    with open(path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            plan.append(row)
    return plan


def default_starter_plan(asin, role):
    """没给 plan 文件时,生成最小 starter 计划(7 维各 1-2 题)。
    
    实际使用应该先读 Listing 跑 product profile 再生成,这里只是兜底。
    """
    base = [
        ("size_advice_by_body", "I'm 5'6 and 140 lbs, what size should I order?", "size"),
        ("fit_silhouette", "Is this oversized or fitted?", "fit"),
        ("fabric_composition", "What's the fabric of this dress?", "fabric"),
        ("fabric_weight_thickness", "Is the fabric thick or see-through?", "fabric"),
        ("occasion_work_office", "Is this dress office appropriate?", "occasion"),
        ("care_wash_method", "Can I machine wash this?", "care"),
        ("care_shrinkage", "Will it shrink after washing?", "care"),
        ("complaint_color_mismatch", "Is the color accurate to the photos?", "complaint"),
        ("vs_competitor_feature_diff", "How does this compare to similar dresses?", "vs_competitor"),
    ]
    plan = []
    for i, (sub, q, dim) in enumerate(base, 1):
        plan.append({
            'planned_question_id': f"{role.upper()[:3]}-{asin[:6]}-Q{i:03d}",
            'asin': asin,
            'product_role': role,
            'question_text': q,
            'question_origin': 'category_coverage_generated',
            'profile_signal': 'apparel_minimum_set',
            'primary_dimension': dim,
            'sub_category': sub,
            'priority_score': '3',
        })
    return plan


# ============================================================
# 主流程
# ============================================================

async def run_one_asin(cdp, asin, role, marketplace, plan, output_dir, persona="default"):
    rows = []
    blocker = None
    
    # 1. 登录检查
    login = await state_login_check(cdp)
    if not login['logged_in']:
        blocker = {
            'reason': 'amazon_buyer_login_required',
            'evidence': login['evidence'],
            'message': '浏览器没登录 Amazon 买家账号,请先跑 scripts/login_amazon.py 或通过 chat 通道提供登录方式'
        }
        return rows, blocker
    
    # 2. 检查手机号验证
    if await state_check_mobile_required(cdp):
        blocker = {
            'reason': 'mobile_number_verification_required',
            'message': 'Amazon 要求添加手机号,请通过 chat 通道提供手机号 → 提交后回复"已添加手机号" → 提供短信验证码'
        }
        return rows, blocker
    
    # 3. 导航
    nav = await state_navigate_asin(cdp, asin, marketplace)
    if not nav['ok']:
        blocker = {
            'reason': 'page_mismatch',
            'message': f"导航到 {asin} 失败,实际 ASIN: {nav.get('actual_asin')}",
        }
        return rows, blocker
    
    # 4. Listing 快照(简化版 — 完整 profile 应在外部跑)
    snapshot = await state_listing_snapshot(cdp)
    snapshot_path = Path(output_dir) / f"listing_snapshot_{asin}.json"
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2))
    
    # 5. Rufus 探针
    probe = await cdp.eval(PROBE_RUFUS_JS)
    if not all([probe.get('opener'), probe.get('panel') or True, probe.get('input') or True]):
        # opener 必须有,input/panel 在 ask 时再开
        if not probe.get('opener'):
            blocker = {
                'reason': 'rufus_not_visible',
                'message': f'ASIN {asin} 上没找到 Rufus 入口按钮(可能被站点 A/B 屏蔽)',
            }
            return rows, blocker
    
    # 6. 逐题抓取
    print(f"  开始抓 {len(plan)} 题")
    for idx, q in enumerate(plan, 1):
        capture_id = f"{q['planned_question_id']}-CAP"
        row = CaptureRow(
            capture_id=capture_id,
            capture_date=datetime.now().isoformat(),
            marketplace=marketplace,
            product_role=role,
            asin=asin,
            product_url=nav['url'],
            persona_label=persona,
            login_status='logged_in',
            planned_question_id=q['planned_question_id'],
            question_origin=q.get('question_origin', ''),
            profile_signal=q.get('profile_signal', ''),
            primary_dimension=q.get('primary_dimension', ''),
            sub_category=q.get('sub_category', ''),
            raw_question=q['question_text'],
            normalized_question=normalize_question(q['question_text']),
        )
        
        try:
            result = await ask_rufus(cdp, q['question_text'])
        except Exception as e:
            result = {'ok': False, 'reason': f'js_exception: {str(e)[:80]}'}
        
        row.submit_attempt_count = 1
        row.submit_method = 'click_dispatch'
        
        if result.get('ok'):
            row.capture_status = 'answered'
            row.raw_answer = result['answer']
            row.answer_length_chars = result['answerLength']
            row.follow_up_prompts = ' | '.join(result.get('followups', []))
            row.selector_strategy = result.get('selectorStrategy', '')
            
            # 简单分类 answer_type
            ans_low = row.raw_answer.lower()
            if 'instead' in ans_low and 'consider' in ans_low:
                row.answer_type = 'alternative_recommendation'
            elif re.search(r'\$\d+', row.raw_answer) and 'compar' in ans_low:
                row.answer_type = 'comparison_table'
            elif 'customers' in ans_low or 'reviewers' in ans_low or 'buyers' in ans_low:
                row.answer_type = 'review_summary'
            elif '$' in row.raw_answer:
                row.answer_type = 'price_history'
            else:
                row.answer_type = 'direct_answer'
            
            print(f"  [{idx}/{len(plan)}] ✓ {row.answer_length_chars} 字 | {row.answer_type}")
        else:
            reason = result.get('reason', 'unknown')
            if reason in {'submit_not_acknowledged', 'answer_stabilization_timeout', 'first_answer_timeout'}:
                row.capture_status = 'question_only'
            else:
                row.capture_status = 'blocked'
            row.failure_reason = reason
            row.answer_confidence = 'none'
            print(f"  [{idx}/{len(plan)}] ✗ {reason}")
        
        rows.append(row)
        
        # 每 5 题关一次面板,减上下文污染
        if idx % 5 == 0:
            await close_rufus_panel(cdp)
        
        await asyncio.sleep(2)  # UI 节流,不是反封
    
    return rows, blocker


def write_csv(rows, path):
    if not rows:
        return
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(asdict(r))


def write_health(asin_results, path):
    health = {
        'capture_date': datetime.now().isoformat(),
        'asins': {},
    }
    for asin, (rows, blocker) in asin_results.items():
        statuses = {}
        for r in rows:
            statuses[r.capture_status] = statuses.get(r.capture_status, 0) + 1
        health['asins'][asin] = {
            'total': len(rows),
            'statuses': statuses,
            'blocker': blocker,
            'success_rate': round(statuses.get('answered', 0) / len(rows), 2) if rows else 0,
        }
    Path(path).write_text(json.dumps(health, ensure_ascii=False, indent=2))


async def main_async(args):
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    asins = args.asins.split(',') if args.asins else [args.asin]
    roles = args.roles.split(',') if args.roles else [args.role]
    if len(asins) != len(roles):
        print("✗ asin 和 role 数量不匹配")
        sys.exit(2)
    
    ws_url = await get_cdp_ws_url()
    print(f"CDP: {ws_url}")
    
    asin_results = {}
    
    async with websockets.connect(ws_url, max_size=20_000_000) as ws:
        cdp = CDPClient(ws)
        
        # 拿到第一个 page tab 并激活
        targets = await cdp.send('Target.getTargets')
        page_targets = [t for t in targets['targetInfos'] if t['type'] == 'page']
        if page_targets:
            await cdp.send('Target.activateTarget', {'targetId': page_targets[0]['targetId']})
        
        for asin, role in zip(asins, roles):
            print(f"\n=== ASIN {asin} ({role}) ===")
            
            if args.plan_file:
                plan = [p for p in load_plan_csv(args.plan_file) if p['asin'] == asin]
            else:
                plan = default_starter_plan(asin, role)
                # 截到指定深度
                plan = plan[:args.depth]
            
            print(f"  题数: {len(plan)}")
            
            try:
                rows, blocker = await run_one_asin(
                    cdp, asin, role, args.marketplace, plan, output_dir, args.persona
                )
                asin_results[asin] = (rows, blocker)
                
                # 单 ASIN 结果立即落盘(防中途崩)
                write_csv(rows, output_dir / f'capture_{asin}.csv')
                
                if blocker:
                    print(f"  ⚠ blocker: {blocker['reason']} - {blocker['message']}")
                    # 遇到全局 blocker(login/mobile)就停,不继续后面 ASIN
                    if blocker['reason'] in {'amazon_buyer_login_required',
                                             'mobile_number_verification_required'}:
                        print("  全局 blocker,停止后续 ASIN")
                        break
            except Exception as e:
                print(f"  ✗ 异常: {e}")
                asin_results[asin] = ([], {'reason': 'exception', 'message': str(e)})
    
    # 合并所有 ASIN 的 row 到一个 baseline.csv
    all_rows = []
    for asin, (rows, _) in asin_results.items():
        all_rows.extend(rows)
    write_csv(all_rows, output_dir / 'capture_baseline.csv')
    write_health(asin_results, output_dir / 'capture_health.json')
    
    print(f"\n✓ 完成。输出在 {output_dir}/")
    print(f"  - capture_baseline.csv ({len(all_rows)} 行)")
    print(f"  - capture_health.json")


def main():
    parser = argparse.ArgumentParser(description='Rufus 单/多 ASIN 抓取(状态机版)')
    parser.add_argument('--asin', help='单个 ASIN')
    parser.add_argument('--asins', help='多个 ASIN,逗号分隔')
    parser.add_argument('--role', default='own', help='own / competitor_1 / ...')
    parser.add_argument('--roles', help='多个 role,逗号分隔(跟 --asins 对应)')
    parser.add_argument('--marketplace', default='com', help='com / co.uk / de / ...')
    parser.add_argument('--depth', type=int, default=15, help='每个 ASIN 抓多少题(无 plan 时)')
    parser.add_argument('--plan-file', help='question plan CSV 路径')
    parser.add_argument('--persona', default='default', help='persona 标签')
    parser.add_argument('--output-dir', default='out', help='输出目录')
    args = parser.parse_args()
    
    if not args.asin and not args.asins:
        print("✗ 必须给 --asin 或 --asins")
        sys.exit(2)
    
    asyncio.run(main_async(args))


if __name__ == '__main__':
    main()
