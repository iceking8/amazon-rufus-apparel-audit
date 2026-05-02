# 服装类目 Rufus Question Taxonomy

服装跟通用品类不一样,买家在 Rufus 上反复问的就那几件事。这个文件把服装 buyer concern 切成七维,每维给细分类、典型问法、优先级触发条件。提问计划必须按这个体系打标,报告里也按这个体系汇总。

## 七维总览

| 维度代号 | 维度名 | 决定 Listing 哪里改 | 默认权重 |
|---|---|---|---|
| `size` | 尺码 | 尺码表图、A+ Size Guide、bullet 尺码行 | ★★★★★ |
| `fit` | 版型/廓形 | 主图正侧背、A+ 模特实穿、bullet 第 1 条 | ★★★★★ |
| `fabric` | 面料/手感/透气 | 图4面料近景、A+ 面料模块、bullet 面料行 | ★★★★ |
| `occasion` | 场合/活动适配 | 场景图、A+ 场景模块、bullet 场合行 | ★★★★ |
| `care` | 洗护/缩水/起球 | 洗标图、A+ 洗护模块、bullet 洗护行 | ★★★ |
| `complaint` | 差评/退货原因 | FAQ 图、A+ FAQ 模块、bullet 风险预期管理 | ★★★★★ |
| `vs_competitor` | 竞品对比/系列对比 | A+ Comparison Chart、自家系列对比图 | ★★★★ |

★ 越多代表对服装类目转化的影响越大。`size` / `fit` / `complaint` 三项是死穴——服装退货 60% 以上都来自这三项。

## 维度细分 + 典型问法

### 1. `size` — 尺码

| 子类 | 典型 Rufus 问法 | profile_signal 触发条件 |
|---|---|---|
| `size_chart_clarity` | "Where's the size chart?" / "What does M correspond to in inches?" | Listing 没尺码表 或 表只在某个图角落 |
| `size_advice_by_body` | "I'm 5'5\" 130lbs, which size?" / "我 165cm 60kg 穿 M 还是 L?" | 没"模特身高+穿着尺码"标注 |
| `size_run` | "Does this run small/large/true to size?" | review 反复出现 runs small/large |
| `size_extremes` | "Available in plus size?" / "Petite friendly?" | variants 没覆盖 XS/XXL |
| `size_consistency` | "Are sizes consistent between colors?" | 多色多版本 SKU |

**优先级加分**:任何 `size_*` 子类自动 +1。如果竞品 Q&A 反复出现且自家 Listing 没尺码表图,直接拉到 5 分(critical)。

### 2. `fit` — 版型/廓形(独立成轴,不要跟 size 混)

服装买家把 size 和 fit 分得很清:size 是"我穿几号",fit 是"这件衣服本身是什么形状"。

| 子类 | 典型 Rufus 问法 | profile_signal 触发条件 |
|---|---|---|
| `silhouette` | "Is this oversized or fitted?" / "Loose or tight?" | bullet/title 没明确写 oversized/relaxed/slim/regular |
| `length` | "How long is the dress?" / "Where does it hit on a 5'6\" person?" | 没标"模特身高 + 衣长落点" |
| `cut_detail` | "High-waisted?" / "Cropped?" / "Drop shoulder?" | 详情没标关键剪裁特征 |
| `body_shape_fit` | "Good for pear shape?" / "Hourglass friendly?" | A+ 没说明适合体型 |
| `stretch` | "Is it stretchy?" / "How much give?" | 面料没标弹力/spandex 含量 |
| `tightness_zones` | "Tight in the chest?" / "Roomy in the hips?" | 没局部松紧描述 |

**版型独立维度的原因**:你勾了"版型"是头疼项,意味着这是首要差异化点。版型描述差,买家就只能赌,赌输就退货。

### 3. `fabric` — 面料/手感/透气

| 子类 | 典型 Rufus 问法 | profile_signal 触发条件 |
|---|---|---|
| `composition` | "What's it made of?" / "100% cotton?" | bullet 没成分百分比 |
| `weight_thickness` | "Is it thick or thin?" / "See-through?" | 没克重数据 / 没正反对比图 |
| `breathability` | "Breathable for summer?" / "Sweaty in this?" | 没透气性描述 |
| `softness_feel` | "Is it soft or scratchy?" / "Itchy?" | review 提到 itchy/scratchy 但 Listing 没回应 |
| `lining` | "Is it lined?" / "Need to wear a slip?" | 单层薄面料没说明衬里情况 |
| `pilling_risk` | "Does it pill?" / "起球吗?" | 化纤/羊毛混纺类 |
| `stretchiness` | "Stretchy?" — 跟 fit/stretch 重复时,只标主分类 | 同上 |

### 4. `occasion` — 场合/活动适配

| 子类 | 典型 Rufus 问法 | profile_signal 触发条件 |
|---|---|---|
| `work_office` | "Office appropriate?" / "Business casual?" | 通勤/职业向 SKU 没标办公场景 |
| `formal_event` | "Wedding guest dress?" / "Cocktail party?" | 礼服/连衣裙类 |
| `casual_daily` | "Good for daily wear?" | 基础款 |
| `sports_specific` | "Yoga?" / "Running?" / "Hot yoga?" | 运动品类必问 |
| `weather_season` | "Warm enough for winter?" / "Summer hot weather?" | 季节性强的品类 |
| `travel` | "Wrinkle-resistant for travel?" / "Packable?" | 出差/旅行场景 |
| `dress_code_fit` | "Allowed at golf course?" / "Gym dress code OK?" | 有 dress code 限制的运动类 |
| `pregnancy_postpartum` | "Maternity friendly?" / "Postpartum?" | 宽松款/弹力款 |

### 5. `care` — 洗护/缩水/起球

| 子类 | 典型 Rufus 问法 | profile_signal 触发条件 |
|---|---|---|
| `wash_method` | "Machine washable?" / "Hand wash only?" | 洗标信息缺失 |
| `shrinkage` | "Will it shrink?" / "How much shrinkage?" | 全棉/羊毛/亚麻类 |
| `colorfastness` | "Will it bleed?" / "Fade after wash?" | 深色/印花类 |
| `iron_dryclean` | "Need ironing?" / "Dry clean only?" | 高维护面料 |
| `wrinkle_resistance` | "Wrinkle-resistant?" | 出差场景 / 商务衬衫类 |
| `durability` | "How long does it last?" / "After 10 washes?" | 价格中高位需要解释耐久性 |

### 6. `complaint` — 差评/退货原因(反向触发)

这是从 review 1-3 星反推应该回答的问题,不等买家在 Rufus 问。

| 子类 | 典型 Rufus 问法 | profile_signal 触发条件 |
|---|---|---|
| `color_mismatch` | "Is the color accurate?" / "Looks different from photos?" | review 反复说色差 |
| `quality_concern` | "Is the stitching good?" / "Cheap feeling?" | review 提质量差 |
| `defect_rate` | "Common defects?" / "Loose threads?" | 1-2 星集中在做工 |
| `delivery_packaging` | "Wrinkled on arrival?" / "Bad packaging?" | review 提到包装问题 |
| `return_difficulty` | "Easy to return if wrong size?" | 没明确退换政策 |
| `false_advertising` | "Photos misleading?" | 主图过度修图被吐槽 |

**优先级**:任何 `complaint_*` 自动 +1,且如果是退货 top reason 直接拉满 5 分。

### 7. `vs_competitor` — 竞品对比/系列对比

| 子类 | 典型 Rufus 问法 | profile_signal 触发条件 |
|---|---|---|
| `vs_named_brand` | "How does this compare to [Brand X]?" | 有强势同类竞品 |
| `vs_price_tier` | "Why is this more expensive than similar ones?" | 价位高于均值 |
| `series_difference` | "Difference between [model A] and [model B]?" | 自家有多个相近 SKU |
| `material_grade_comparison` | "Better fabric than the cheaper version?" | 跟低价竞品的差异化 |
| `feature_diff` | "Has X feature that [Brand Y] doesn't?" | 独特卖点 |

**注意**:Rufus 给出 `alternative_recommendation`(说"你不如买 X")时,要单独标 `gap_type=rufus_redirect_risk`,这是非常严重的信号——意味着 Rufus 在主动把流量推给别人。

## Question Origin 标签(沿用 audit 体系)

每条计划提问标这五种之一:

- `rufus_starter`:Rufus 面板上自带的起始问题
- `rufus_followup`:点完一题后 Rufus 自动生成的后续问题
- `product_profile_generated`:你看完 Listing 自己生成的问题(必须挂 `profile_signal`)
- `category_coverage_generated`:服装七维标准覆盖问题(用来填空白)
- `user_supplied`:卖家自己点名要测的问题

## Capture Status(每行必标)

- `answered`:问题和答案都拿到
- `question_only`:问题拿到了答案没出来
- `blocked`:Rufus 没出现 / 登录墙 / CAPTCHA
- `duplicate`:跟已有行近似重复
- `out_of_scope`:Rufus 答的是别的产品 / 通用建议 / 推荐了别人

## 覆盖标签(对自家 Listing)

每个买家担忧 vs 你 Listing,标其中一个:

- `strong`:Listing 受控内容(标题/bullet/图/A+)清晰回答了
- `partial`:回答了但藏得深 / 表述模糊
- `weak`:有暗示但买家可能仍困惑
- `missing`:完全没答
- `contradicted`:Listing 跟 review/Q&A 自相矛盾(最危险,可能引发投诉)
- `review_only`:review 答了,但你的受控内容没答(Rufus 会引用,但你失去主动权)
- `not_applicable`:这个问题对你的 SKU 不适用

## Answer Type(Rufus 答案形态)

每条 answered 行标其中一个,用来决定怎么用:

- `direct_answer`:直接事实回答
- `review_summary`:Rufus 在引用买家评价
- `comparison_table`:Rufus 在做对比表(高威胁,看下面)
- `alternative_recommendation`:Rufus 推荐了别的产品(最高威胁)
- `price_history`:Rufus 在讲价格走势
- `activity_fit`:Rufus 在判断活动/场合适配
- `mixed`:多种混合

**遇到 `comparison_table` 或 `alternative_recommendation`**:这是 Rufus 在帮竞品/系列内对手抢你流量,必须在报告里单独成节列出。

## 优先级 1-5 加分制

每个 buyer concern 起步 1 分,命中以下条件每条 +1,封顶 5:

- +1:命中"尺码 / 版型 / 差评" 三大死穴(`size_*` / `fit_*` / `complaint_*`)
- +1:同一担忧在 ≥ 2 个竞品 Q&A 都被问到(category_concern,不是单家问题)
- +1:你 Listing 覆盖标签是 `missing` / `weak` / `contradicted` / `review_only`
- +1:可以在一次 Listing 更新内修复(改图/改 bullet/加 A+ 模块)
- +1:Rufus 答案是 `comparison_table` 或 `alternative_recommendation`(主动伤害)

| 分数 | 标签 | 含义 |
|---|---|---|
| 5 | critical | 下次 Listing 更新必改 |
| 4 | high | 排进本月迭代 |
| 3 | medium | 排进季度迭代 |
| 2 | low | 看到顺手改 |
| 1 | watch | 仅观察 |

## Gap Type(报告用的 issue 标签)

- `missing_answer`:竞品答了我家没答
- `weak_answer`:答了但说服力不够
- `buried_answer`:答了但藏在低曝光位置(比如只在 description 里写了)
- `review_risk`:review 暴露的问题受控内容没回应
- `contradiction`:受控内容和 review/Q&A 自相矛盾
- `persona_gap`:没说清楚是给谁穿的(COSMO 要的是这个)
- `comparison_gap`:没有客观对比点,Rufus 只能拿别人对比
- `visual_gap`:答案应该用图说,但缺图
- `claim_risk`:回答会触发 compliance(医疗/环保/安全声明)
- `capture_gap`:抓取本身不全,先别下结论
- `rufus_redirect_risk`:Rufus 主动推荐了别的产品
- `review_signal_gap`:Rufus 引用了 review 里的话,但 Listing 受控内容没说

## 服装类目 Minimum Question Set

每个 ASIN 至少覆盖以下 8 题(够不到就标 `not_collected`):

1. 一道 `size_*`(尺码建议)
2. 一道 `fit_*`(版型/廓形或长度)
3. 一道 `fabric_*`(成分/克重/透气)
4. 一道 `occasion_*`(典型场景)
5. 一道 `care_*`(洗护)
6. 一道 `complaint_*`(从 review 反推的疑虑)
7. 一道 `vs_competitor_*`(对比类)
8. 一道 `customer_sentiment`(让 Rufus 总结评价)

不到 8 题、且失败原因不是 Rufus 屏蔽的,要在报告里说明放弃哪几题、为什么。
