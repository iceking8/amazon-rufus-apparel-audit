# 服装审计工作流

四阶段必经流程。每阶段产出固定,产出不达标不进入下阶段。

## 阶段 0:任务接收

收集输入(参考 SKILL.md "输入要求"一节)。任何关键信息缺失,先用 chat 问用户,**绝不**用 stdin。

确定**审计模式**:

| 模式 | 触发条件 | 产出 |
|---|---|---|
| `competitor_only` | 用户只给了竞品 | 七维担忧地图 + 下次抓取建议(不能下 gap 结论) |
| `own_vs_competitor` | 自家+竞品都给了 | 完整覆盖矩阵 + 优先级修复清单 + 修改方案 |
| `retest` | 用户给了上次抓取 baseline + 新抓取 | 改动前后对比报告 |

## 阶段 1:Profile(产品档案)

**必经闸门**。读不完档案不许进 Plan 阶段。

按 [product-profiling-apparel.md](product-profiling-apparel.md) 字段逐个产品建档。每个 ASIN 必须读以下区块:

1. title / 价 / 星 / 评数 / 变体
2. Bullets 5 条
3. Product Details
4. 主图 7 张(逐张分类:上身正/上身背/面料/尺码/场景/FAQ/其他)
5. A+ 模块(数量 + 各模块在讲什么)
6. 现有 Q&A 区
7. Review themes(前 50 条 + 1-3 星前 20 条)

每读不到一个区块就标 `not_captured`。

**完成度判断**:

- 服装 10 项关键证据 ≥ 8 项 → `profile_status=complete`
- 5-7 项 → `profile_status=partial`(标注哪些缺,但可继续)
- < 5 项 → `profile_status=blocked`,只出"Listing 起步建议",**不**抓 Rufus

**输出**:`product_profile.json`,字段按 product-profiling-apparel.md。

## 阶段 2:Plan(提问计划)

读完档案后生成提问计划。每条问题必须有:

- `planned_question_id`
- `question_text`
- `question_origin`(rufus_starter / rufus_followup / product_profile_generated / category_coverage_generated / user_supplied)
- `profile_signal`(generated 类必填,引用 profile 哪个字段触发)
- `primary_dimension`(七维代号)
- `sub_category`(taxonomy 子类代号)
- `priority_score`(1-5)
- `ask_order`

**生成规则**:

1. 把每个 ASIN 的 Rufus 面板可见 starter questions 全部加入 plan(标 `rufus_starter`,先抓)
2. 按 [product-profiling-apparel.md] 末尾的"profile 信号→问题"对照表生成 `product_profile_generated`(必带 profile_signal)
3. 检查七维 Minimum Question Set,缺哪维补 `category_coverage_generated`
4. 用户点名要测的题加 `user_supplied`

**配额**:每 ASIN 默认 15-25 条,starter 必抓,生成类按优先级降序。

**输出**:`question_plan.csv`。

## 阶段 3:Capture(抓取)

按 [browser-capture.md](browser-capture.md) 状态机和 [automation-patterns.md](automation-patterns.md) 代码模式跑。

**严格顺序提交**(单 ASIN):

```
verify login → listing snapshot → product profile → question plan
→ for each question:
    submit one question
    wait_thinking → wait_stable
    save row (answered or failed,绝不丢)
    extract followup prompts
    pause briefly
→ save ASIN capture health
→ next ASIN
→ final save → close browser
```

**Sequential Submission Rule**(死规矩):上一题没稳定不许提交下一题。Rufus 多题并行会全部卡 thinking。

**Session 控制**:

- 一个 Chrome session 处理多 ASIN,但每 ASIN 之间关闭 Rufus 面板(qa skill 的"会话重置"思路在合规框架内可用)
- 不要靠这个绕限流,只是为了避免 Rufus 上下文污染

**遇到 blocker 立即停**:

| Blocker | 标签 | 行动 |
|---|---|---|
| 没登录 | `failure_reason=amazon_buyer_login_required` | 通过 chat 问用户登录方式,不用 input() |
| Add a mobile number | `challenge_type=mobile_number_required` | chat 问手机号,提交后回复"已添加手机号",再问短信码 |
| CAPTCHA / 安全警告 | `challenge_type=captcha_or_robot_check` | 直接停,不绕 |
| Rufus 面板不可见 | `failure_reason=rufus_not_visible` | 标 blocked,继续下个 ASIN |
| Thinking 卡住 | `failure_reason=thinking_timeout` | 试一次 Resume response,失败标 question_only |

**输出**:`capture_baseline.csv`(每行一个 Q&A)+ `capture_health.json`。

## 阶段 4:Report(报告)

按 [output-schema-cn.md](output-schema-cn.md) 顺序产出报告。**抓取健康**节先写,失败 > 30% 时整段警告放最前。

### 4.1 担忧地图归类

把 capture_baseline 按七维 + 子类聚合,标记每行的 `concern_scope`:

- `category_concern` — 多家竞品都被问到,这是行业级担忧
- `competitor_specific` — 只在某家被问到,跟它独有的特征/差评相关
- `own_opportunity` — 跟自家产品相关,可在 Listing 内回应
- `unsupported_gap` — 自家 Listing 没拿到或抓取不全,不能下 gap 结论

### 4.2 覆盖判定(逐行)

对每个 `own_opportunity` 担忧,在自家 Listing 受控内容中找证据:

- 找到 → `strong` / `partial` / `weak`
- 没找到但 review 提到 → `review_only`
- 没找到 → `missing`
- 矛盾 → `contradicted`(高危)

### 4.3 优先级打分

按 [apparel-question-taxonomy.md] 的 1-5 加分制,每条给:

- 分数(1-5)
- 标签(critical / high / medium / low / watch)
- gap_type

### 4.4 修改方案生成

对 ≥ 3 分的每条担忧,按 [fix-playbook-apparel.md] 模板生成具体修改。每条必须包含:

- 位置(精确到图N第N屏 / bullet N / A+ Module N)
- 现状(quote 或描述当前 Listing 内容)
- 改成什么(直接给可粘贴的文案)
- 理由(挂回担忧来源行 ID)
- 算法对齐打分(A10/COSMO/Rufus 各高/中/低/无)
- 执行人 + 预计工时

### 4.5 算法对齐汇总

把所有修改建议汇总成一张表(参 [output-schema-cn.md] §8),按总分降序就是执行优先级。

### 4.6 风险与限制

每次报告必写,内容参 [output-schema-cn.md] §9。

### 4.7 回测计划

按 [algo-alignment.md] 末尾的"反向用 Rufus 验证"8 题给到。

**输出**:`report_cn.md`(主报告)+ `coverage_matrix.csv` + `fix_tracker.csv`。

## 浏览器清理

任务结束(完成或 blocker 退出)前,**必须**:

1. 保存所有 capture 行(包括失败行)
2. 保存 capture_health 摘要
3. 关闭浏览器 session(除非用户要求保留以做手动验证)
4. 确认没有 capture-owned 进程留后台

## 阶段间检查

每阶段完成都要回头确认:

- Profile 阶段:档案完整度是不是真到了门槛,还是凑数标 partial
- Plan 阶段:七维 Minimum Question Set 是否覆盖
- Capture 阶段:失败行有没有保留(`question_only` / `blocked` 不许丢)
- Report 阶段:每条 critical / high 修改是不是都对应到具体担忧来源行

发现问题就回到对应阶段补,不要硬出报告。
