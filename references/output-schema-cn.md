# 中文输出 Schema(给运营美工)

报告语言一律中文,但 ASIN、CSV 字段名、维度代号(`size`/`fit`/`fabric`)保留英文以便系统化。每次任务的输出物按下面顺序产出。

## 顶层报告结构

```
1. 抓取健康报告 (Capture Health) ←—— 失败行 > 30% 或自家 Listing 缺失时,这一节必须放最前
2. 执行摘要 (Executive Summary) — 3-5 句话,Top 5 必改点
3. 产品档案 (Product Profiles) — 自家 + 竞品逐个
4. 七维买家担忧地图 (Concern Map by 7 Dimensions)
5. Listing 覆盖矩阵 (Coverage Matrix) — 自家
6. 优先级修复清单 (Priority Fix List)
7. 修改方案分位置:
   7.1 主图 7 张
   7.2 A+ 模块
   7.3 Bullet 5 条
   7.4 Title
   7.5 Search Terms 后台
   7.6 Q&A / Review 引导
8. 算法对齐总结 (A10/COSMO/Rufus 各自获益点)
9. 风险与限制 (Risks & Limitations) — 不能保证什么
10. 回测计划 (Retest Plan)
```

## 1. 抓取健康报告 模板

```markdown
## 抓取健康

- 任务时间:2025-XX-XX
- 站点:US
- 产品数:自家 1 + 竞品 4
- 计划提问数:120
- 实际成功(answered):95(79%)
- question_only:15(12.5%)
- blocked:8(6.7%)
- duplicate / out_of_scope 排除:2 + 0
- 主要失败原因:Rufus 在 ASIN B0XXX 上 5 次 thinking_timeout
- 是否影响结论:不影响,核心七维都有 ≥ 3 行有效证据
- 自家 Listing 是否拿到:是 / 否
```

如果失败率 > 30% 或自家 Listing 拿不到,在这一节直接给警告:`数据不足以支撑 gap 分析,本次报告只能给到竞品担忧地图。建议:[具体的下一步抓取建议]`。

## 2. 执行摘要 模板

```markdown
## 执行摘要

**最高优先级修改 5 条**:

1. 【主图 5】加模特身高对照 → 解决退货 top 1 原因(尺码)
2. 【A+ Module 6】新增 FAQ 模块 → Rufus 现在引竞品答案,我们没素材
3. 【Bullet 1】改成"为通勤妈妈设计的 A 字版型" → COSMO 没认到目标人群
4. 【主图 7】新增 FAQ 图,加 6 条高频问答
5. 【主图 4】面料近景缺克重和弹力数据

**关键发现**:

- 七维中 `fit` 和 `size` 是大坑,竞品 3/4 家都答得比我家好
- 一个竞品的 Rufus 答案出现"alternative_recommendation"指向了另一家——同时也是机会(说明 Rufus 在主动推荐,只要 Listing 改对它也会推我)
- review 高频出现"runs small"但 Listing 没回应

**预计影响**:全部修完后,Rufus 在七维标准问题上引用我家 Listing 的概率从 X% 提升至 Y%(回测可验证)
```

## 3. 产品档案 表格

每个产品一段(role / asin / 关键属性 + missing evidence 列表),用 [product-profiling-apparel.md](product-profiling-apparel.md) 的字段。

## 4. 七维担忧地图

按七维(size / fit / fabric / occasion / care / complaint / vs_competitor)分块,每块给一张表:

| 子类 | 哪几家被问到 | 典型问法 | 答案类型 | 我家是否被问到 | 我家答得如何 |
|---|---|---|---|---|---|
| size_advice_by_body | C1 / C2 / C3 | "5'5" 130lbs which size?" | direct_answer | 是 | 弱(没模特身高) |
| ... |

## 5. 覆盖矩阵 表头(中文版)

```csv
担忧描述,维度,优先级,优先级标签,我家覆盖,标题证据,bullet证据,图片证据,A+证据,review证据,gap类型,改哪里,具体怎么改,预期Rufus收益,信心
```

## 6. 优先级修复清单 模板

按优先级分桶,每桶按位置(主图 / A+ / bullet / title)再分:

```markdown
### Critical(5 分)— 本周必改

【M5-1】主图 5 加模特身高对照
- 维度:size / fit
- 现状:只有尺码表,无身高
- 改成:加 "Model 5'8" wearing S, Bust 33"/Waist 25"/Hip 35""
- 算法对齐:A10 中 | COSMO 低 | Rufus 高
- 执行:美工 / 工时 30 分钟

【B1-1】Bullet 1 改成场景人群版
...
```

## 7. 修改方案分位置(运营美工执行视图)

### 7.1 主图修改清单

按图位号(图1-图7)逐张列。每图一段:

```markdown
**图 1(主图)**
- 状态:✅ 已合规 / ⚠ 需要小改 / ❌ 必须重拍
- 修改点 1:[具体]
- 修改点 2:[具体]
```

### 7.2 A+ 修改清单

按模块号列,**新增模块**的标 [新增],**改写模块**的标 [改写]。

### 7.3 Bullet 5 条逐条改写

直接给前后对比:

```markdown
**Bullet 1**
- 现:Beautiful midi dress for women perfect for any occasion
- 改:RELAXED-FIT MIDI DRESS FOR WORKING MOMS — A flowy A-line silhouette that hides postpartum tummy without sacrificing style. Office to dinner without changing.
- 理由:COSMO 需要人群+场景,Rufus 需要具体问题陈述
```

### 7.4 Title

给保守版 + 平衡版(推荐)+ 激进版三个,标注哪个用什么场景。

### 7.5 Search Terms

直接列 250 字符候选,按品类/场景/人群/特征四块分。

### 7.6 Q&A / Review 引导

- 给 5-10 条建议老客户问的问题模板
- 给售后卡 / 邮件文案模板(中文 + 英文版)

## 8. 算法对齐总结 表

把所有修改建议汇总成一张表:

| 修改编号 | 位置 | A10 收益 | COSMO 收益 | Rufus 收益 | 总分 |
|---|---|---|---|---|---|
| M5-1 | 主图 5 | 中 | 低 | 高 | 7/9 |
| B1-1 | Bullet 1 | 中 | 高 | 高 | 8/9 |
| ... |

总分降序排,这就是执行优先级。

## 9. 风险与限制(必写)

```markdown
## 风险与限制

**这份报告不保证**:

- 不保证 BSR / 排名提升 — 算法吃多个信号,本报告只覆盖内容侧
- 不保证 Rufus 一定推荐你 — Rufus 还吃 review 量、销量、价格等
- Title 大改有重置 search rank 风险 — 建议先用保守版 A/B
- 抓取数据有时效性 — Rufus 答案可能 1-2 月后变化

**已知数据局限**:

- 抓取时间:[日期]
- 抓取站点:[US/UK/...]
- 失败行占比:[X%]
- 没拿到的 Listing 模块:[列出]
```

## 10. 回测计划

```markdown
## 回测计划

**第 1 周(立刻)**:Listing 改完后,亲自跑 [algo-alignment.md] 里的 8 题验证 Rufus 引用情况

**第 1 个月**:观察以下指标变化
- BSR(子类目)
- conversion rate(SP-API 后台)
- 退货率(尤其尺码相关退货率)
- review 增长速度
- 1-3 星 review 的主题分布

**第 3 个月**:重新抓 Rufus(同样 30 题),对比改动前后:
- 七维覆盖标签变化(missing → partial → strong)
- 是否还出现 alternative_recommendation
- review 引用语言是否变化

**第 6 个月**:看是否还能产出新的 gap(可能竞品也在改)
```

## CSV 表头(给运营导 Excel)

### Capture Baseline(原始抓取行)

```csv
capture_id,capture_date,marketplace,product_role,asin,product_url,persona_label,login_status,challenge_type,source_depth,parent_question_id,question_origin,profile_signal,capture_status,failure_reason,raw_question,normalized_question,raw_answer,answer_summary,answer_length_chars,answer_confidence,answer_type,follow_up_prompts,primary_dimension,sub_category,buyer_concern_cn,competitor_strength,competitor_mentions,price_evidence,review_evidence_summary,concern_scope,recovery_action,notes
```

注意:`primary_dimension` 取值是七维代号(`size`/`fit`/`fabric`/`occasion`/`care`/`complaint`/`vs_competitor`),`sub_category` 是 [apparel-question-taxonomy.md] 里的子类代号(如 `size_advice_by_body`)。

### Coverage Matrix(给运营做决策)

```csv
担忧编号,担忧描述,维度,子类,优先级,优先级标签,我家覆盖,标题证据,bullet证据,图证据,A+证据,review证据,gap类型,修改位置,具体修改,A10收益,COSMO收益,Rufus收益,总分,执行人,预计工时,信心
```

### Fix Tracker(给运营跟进改动)

```csv
修改编号,优先级,位置,现状描述,修改后,担忧来源行ID,执行人,预计工时,deadline,完成状态,完成时间,回测时间,回测结果
```
