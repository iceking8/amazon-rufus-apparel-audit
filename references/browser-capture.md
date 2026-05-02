# 浏览器自动化护栏

这个文件管"行为契约":什么时候必须停、什么时候可以继续、答案怎么算稳定。具体代码在 [automation-patterns.md](automation-patterns.md)。

## 状态机

每个抓取任务必须按这个状态机走:

```
ready
  → login_state_check
  → listing_snapshot
  → product_profile
  → question_plan
  → submit_one_question
  → waiting_for_thinking
  → waiting_for_answer_stable
  → capture_answer
  → capture_followups
  → ready (loop)
  → final_save
  → close_browser

login fail → blocker_save → user_message_for_login → close_browser

mobile_required
  → blocker_save → user_message_for_phone → submit_phone
  → user_message_added_phone(回复"已添加手机号")
  → user_message_for_sms → submit_sms → login_state_check
```

**禁止**:`submit_one_question` 状态绝不允许在前一题还在 `waiting_for_thinking` 或 `waiting_for_answer_stable` 时进入。

## 登录状态闸门

抓任何 Listing 内容或找 Rufus 之前,先验证登录:

- 看 header 有没有 "Hello, sign in"
- 看是不是被重定向到 /ap/signin
- 看 `#nav-link-accountList-nav-line-1` 文本是不是 "Hello, [name]"

不在登录态:

1. 立刻停所有抓取
2. 存 `login_status=not_logged_in`
3. 通过 chat 问用户:"浏览器没登录 Amazon 买家账号,请提供登录方式(账号/密码 + OTP/TOTP 工作流,通过 Anthropic 的 secret 通道或环境变量传入)"
4. **不用 stdin / input() / 阻塞 prompt**
5. 关 capture-owned 浏览器(除非用户在那个浏览器里手动登录)

## 手机验证闸门

Amazon 弹 "Add a mobile number" / 手机号验证页时:

1. 立刻停所有 Rufus / Listing 抓取
2. 存 `challenge_type=mobile_number_required`
3. 通过 chat 问用户手机号(不是 stdin)
4. 拿到后填进表单提交,**不打印手机号到 log**
5. 提交成功后给用户回:**`已添加手机号`**(原文,中文)
6. Amazon 发短信码后,通过 chat 问用户短信码
7. 拿到后填进去,**不打印**,只用一次,之后从内存丢弃
8. 验证清除后回到 `login_state_check`

如果手机号或短信码被拒绝,标 blocker 停止,不要循环重试。

## 抓取前 Listing 快照

在任何 Rufus 交互之前,从产品页拿到这些(对应 [product-profiling-apparel.md] 字段):

- title / brand / 价 / 星 / 评数
- variants / size 范围 / colors
- bullets 5 条原文
- product details 表
- 主图列表(各张 alt text + 顺序)
- A+ 模块标题列表
- 现有 Q&A 区前 N 条

读不到的存 `not_captured`,**不猜**。

## Rufus 元素探针

每次进新页面用这些 selector 探一遍,verify 当前页可用再批量提问:

```javascript
const openButton = document.querySelector('.nav-rufus-disco-text, .nav-rufus-disco');
const panel = document.querySelector('#nav-flyout-rufus');
const input = document.querySelector('#rufus-text-area, textarea[aria-label*="Rufus"]');
const submit = document.querySelector('#rufus-submit-button, [data-testid="rufus-submit"]');
```

验证:

1. open button 可见且能打开面板
2. panel 可见且属于当前页
3. input 在 panel 内或 Rufus form 内
4. submit 跟 input 同一 form
5. 跑一道探针问题,确认产生一个新的 user turn,**再**批量抓

不通过 → 标 `failure_reason=selector_verification_failed`,停掉这个 ASIN。

## 答案稳定判定

不要把整个 panel.innerText 当答案。**优先级**:

1. 最新 assistant turn 容器 > 最新 user question 容器 > panel 文本 fallback
2. 用 panel 文本 fallback 时,标 `selector_strategy=panel_text_fallback`,在 notes 里写明可能含历史

**稳定条件**(必须全部满足):

- 没有 `Thinking...` / loading 指示
- 没有 `Resume response` 按钮
- 答案文本长度连续两次检查不变
- follow-up 提示按钮已出现 或 UI 不再更新

**不要**靠"completed generating"这种字符串,DOM 里不一定有。
**不要**把 "Would you like" 当结束标志,可能是答案的一部分。
**不要**用硬编码 wait count 当唯一完成判据。

长答案(comparison_table / alternative_recommendation / price_history)需要更长 timeout。

## 卡死恢复

多个问题都卡 `Thinking...` 时:

1. 立刻停止提交新问题
2. 找可见的 `Resume response` 按钮
3. 点一次,等稳定
4. 成功 → 标 `recovery_action=resume_response`
5. 失败 → 标 affected rows `question_only` + `failure_reason=thinking_timeout`
6. 重载是最后手段,Rufus 重载后历史可能仍然坏

## 单题失败回退预算

每题最多试 3 种提交方式:

1. 表单 submit 控件 click(JS click + dispatchEvent)
2. 在 input 里按 Enter(CDP keyboard / Playwright press)
3. CDP/Playwright 模拟用户输入

3 种都失败 → 行 `capture_status=question_only`,`failure_reason=submit_not_acknowledged`,`submit_attempt_count` / `submit_method` 写到行里,**不丢**。

## 进度报告(给用户的)

只在以下里程碑报进度,**不**把每个 CDP probe 都报给用户:

- 登录验证完成
- product profile 保存完成
- question plan 生成完成(列出题数)
- 每 5 条 answered 行
- 出现 blocker(立刻报)
- 单 ASIN 完成
- 所有 ASIN 完成

## 循环死锁检测

连续 3 次浏览器 check 没有任何状态变化(没新答案、没新 follow-up、页面没变)→ 停掉,保存当前结果,报告 blocker。

## 浏览器清理

任务完成或 blocker 退出之前必须:

1. 保存全部 answered + 失败行 + capture_health
2. 关闭 active page / session
3. 确认没有 capture-owned 进程留在后台
4. session 持久化目录(`/tmp/chrome-profile`)保留以便下次免登录,但浏览器进程要关

## 数据捕获最小集

每行 answered 至少存:

- raw_question(原文)
- normalized_question(去重用)
- raw_answer(全文,不裁剪)
- answer_length_chars
- answer_type(direct_answer / review_summary / comparison_table / alternative_recommendation / price_history / activity_fit / mixed)
- follow_up_prompts(数组)
- review_evidence_summary(Rufus 引用了哪些 review 句子)
- competitor_mentions(Rufus 提到了哪些其他产品/品牌)
- price_evidence(Rufus 给出的价格信息)
- recovery_action(如果有)
- selector_strategy
