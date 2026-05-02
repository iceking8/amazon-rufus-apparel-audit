# 抓取故障排查

每个故障都有对应的失败码,行不丢。

## 通用故障对照表

| 现象 | 可能原因 | 应该记录什么 |
|---|---|---|
| 抓取的题完全跟产品无关(都是通用品类问题) | profile 阶段被跳过,Listing 没读 | `profile_status=partial`,补 `question_origin`,记录哪些 profile 字段缺失 |
| Rufus panel 看不见 | 站点/账号/浏览器/区域/A/B 测试问题 | `capture_status=blocked`、`failure_reason=rufus_not_visible` |
| 问题问出去了,答案不出现 | 加载失败、网络问题、面板状态异常 | `capture_status=question_only`,保留 raw_question |
| 后面几题全卡 `Thinking...` | 题没等稳就连续提交了 | 停队列,试一次 Resume response,未解决的标 `question_only` |
| 同一题被反复问 | follow-up 循环 / starter 重复 | `capture_status=duplicate`,notes 里 link 到主行 |
| Rufus 答的是别的产品 | 赞助模块、对比飘移、页面状态飘移 | `capture_status=out_of_scope` |
| Rufus 给通用品类建议 | 没 grounding 到当前 ASIN | `answer_confidence=low`、`concern_scope=category_concern` |
| 浏览器没登录 | 必须登录才看得见 Rufus | 停,标 `login_status=not_logged_in`,通过 chat 问用户登录方式 |
| 弹 OTP / TOTP | 二次验证 | 走 pre-auth 工作流;否则停 |
| 弹 "Add a mobile number" | 账号安全验证 | 停,标 `challenge_type=mobile_number_required`,问手机号 → "已添加手机号" → 问短信码 |
| CAPTCHA / robot check / 安全警告 | 平台风控 | **不绕**,停止 |
| 多次 CDP 探针没产出 | automation 在死循环 polling | 连续 3 次无变化 → 停,标 `no_state_progress` |
| `el.click()` 没反应 | React 事件链没触发 | 用 native event setter + dispatchEvent 序列重试 |
| 等"completed generating"等不到 | 这字符串不在当前 DOM 里 | 改成基于状态判定:答案稳定 + 没 thinking + 没 resume |
| selector `.rufus-papyrus-turn` 拿不到东西 | 动态 class 变了 | 用 verified selector,先跑探针 |
| 答案在"Would you like"被截断 | 把 follow-up 措辞当结束标 | 抓全文,follow-up 单独 parse |
| 答案里混着旧问题/按钮/多轮 | 把整个 panel.innerText 当答案 | 用最新 assistant turn selector,fallback 时标 `selector_strategy=panel_text_fallback` |
| ASIN 请求结果是品类研究 | 跳到了搜索页而非 ASIN 页 | 重新从 `/dp/{ASIN}` 跑,旧行标 category-level only |
| 长答案/对比答案卡住 | 答案太长或后端搜索超时 | 用更长的 stage timeout + 行级失败而不是阻塞整个 run |
| 失败的题"消失了" | 没 retry 也没保留 | 失败也要入库,带 attempt 数、方法、状态、原因 |
| 跑批中途崩 EOFError | 用了 stdin / input() | 改环境变量 / chat 通道,绝不阻塞 |
| 需要 persona 设置 | 会改 Amazon 账号 profile | 单独 chat 确认,优先在审计表里加 persona 标签而不是改账号 |

## 服装类目专属故障

| 现象 | 可能原因 | 应该记录什么 |
|---|---|---|
| Rufus 答 "I don't have specific size recommendations" | Listing 无尺码表 + 模特身高数据 | `gap_type=visual_gap` 或 `missing_answer`,优先级拉到 5 |
| Rufus 推荐了别的品牌服装 | `alternative_recommendation`,Listing 不够说服 | `gap_type=rufus_redirect_risk`,**单独成节列出** |
| Rufus 答案大量引用某个买家 review 原话 | review 主导,Listing 受控内容缺位 | `gap_type=review_signal_gap`,把那段 review 抓下来,写进 A+ FAQ |
| Rufus 答 "customers say it runs small" | review 强信号,Listing 没回应 | `top_complaint_themes` 加 `runs_small`,优先级 5 |
| Rufus 比较时拿不出我家的差异点 | A+ Comparison Chart 缺 / 没特征化描述 | `gap_type=comparison_gap`,A+ Module 5 必加 |
| Rufus 答 "this dress works for [其他场合]"——但跟 Listing 标的场合不一致 | bullet/A+ 描述不准,Rufus 自由发挥 | `gap_type=persona_gap`,Bullet 1 + A+ Module 1 改 |
| 模特身高问 5 次,Rufus 答都不一样 | Listing 多张图模特不同,Rufus 混乱 | 多模特图必须各自标身高/尺码,A+ Module 2 必须明确 |
| Rufus 给出的色号跟我们 Listing 写的不一致 | review 出现色差吐槽,Rufus 引用 | `gap_type=contradiction`,有合规风险,主图重拍 |

## 报告里怎么呈现这些故障

抓取健康报告(必须最先写)模板:

```
抓取健康
- 任务时间:
- 站点:
- 自家 ASIN:[B0XXXX] - login_status=logged_in
- 竞品 ASIN:[B0YYYY 等]
- 计划提问数:120
- answered:95(79%)
- question_only:15(12.5%)
- blocked:8(6.7%)
- duplicate:2 / out_of_scope:0
- 主要失败原因:
  - thinking_timeout × 8(集中在 ASIN B0YYYY 的对比类问题)
  - rufus_not_visible × 5(ASIN B0ZZZZ 整个面板不可见)
- 是否影响结论:不影响。七维 Minimum Question Set 都有 ≥ 3 行有效证据
- 自家 Listing 拿到否:是
- 数据是否足以支撑 gap 分析:是
```

如果数据不足以支撑:

```
⚠ 警告:本次抓取数据不足以支撑完整 gap 分析

原因:
- 自家 Listing 没拿到(login_blocker)
- 抓取失败率 42%

本报告只能提供:
1. 已抓到的竞品担忧地图
2. 下次抓取的改进建议:[具体]

不能提供:
- gap 矩阵
- 优先级修复清单
- 具体修改方案
```

诚实是这个 skill 的硬要求。失败率高就要先告诉用户,**不许**用残缺数据硬出结论。
