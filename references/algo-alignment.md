# A10 / COSMO / Rufus 三算法对齐指南

这个 skill 的最终目的不是"让 Rufus 答得好",是让一份 Listing 优化能**同时**讨好 A10、COSMO、Rufus 三个不同的算法。这篇是为运营理解"为什么这么改"而写的;Claude 在产出修改建议时也必须逐条标注"这次改动 A10/COSMO/Rufus 各自获益什么"。

## 三个算法是什么(高层模型)

### A10 — 传统搜索排序

亚马逊 SP-API 时代到现在的主搜排序逻辑。

**A10 核心信号**:

| 信号 | Listing 体现 |
|---|---|
| 关键词匹配 | title 里有买家搜的词 |
| 转化率 (CR) | 主图、价格、review 数量、A+ |
| 销售速度 | review 量 + 销量 |
| 点击率 (CTR) | 主图、title 前 80 字、review 星级 |
| 后台 search terms | search term 字段填没填 |
| 站外流量 | 联盟、Google Ads 带来的转化 |
| 留评率 | review 数 / 销量 |
| 订单缺陷率 (ODR) | 退货率、差评率 |

**对服装的影响**:A10 仍然吃关键词。title 里没"high waisted dress"、bullet 里没"with pockets",搜这些词时你出不来。但 A10 也吃转化——尺码错了大量退货,A10 会把你打下去。

### COSMO — 语义意图召回(2024 年起)

亚马逊 2024 年发布的认知搜索模型,把买家搜索词背后的"意图、场景、人群"作为召回信号,而不只是关键词字面匹配。

**COSMO 核心信号**:

| 信号 | Listing 体现 |
|---|---|
| 场景描述 | "for office, brunch, weekend" 这种场景词 |
| 人群标签 | "for women 25-40, working moms, petite" |
| 使用动机 | "解决 X 问题"、"适合 Y 时刻" |
| 共现关键词图 | 跟同类高转化产品共享什么属性词 |
| 搜索词→产品语义距离 | Listing 文案能否被映射到买家长尾搜索 |

**对服装的影响**:有人搜"dress to wear to a beach wedding under 100",A10 只能匹"dress"+"beach"+"wedding",COSMO 能理解这是"沙滩婚礼客人穿的、150 美元以下的连衣裙"——意图。Listing 写"midi dress"是 A10 友好,写"flowy midi dress for beach wedding guest under $100"是 COSMO 友好。

**对 COSMO 友好的写法**:

- bullet 第 1 条写**为谁 + 什么场景 + 解决什么**:`Designed for working moms who need a dress that goes from school drop-off to dinner without changing.`
- A+ 加场景模块,直接列"Perfect for: 1) 通勤 2) 周末 brunch 3) 接送孩子 4) 周年纪念"
- 主图集合涵盖至少 3 个场景

### Rufus — 购物 AI 助手

Rufus 现在是 Amazon App 顶部、PC 网页右侧的对话式 AI。买家越来越多直接问 Rufus 而不是搜索。

**Rufus 怎么决定推哪个产品**:

| 信号 | Listing 体现 |
|---|---|
| 受控内容里有可被引用的具体事实 | bullet 里有具体数字、A+ 里有事实陈述 |
| review 里出现的语言 | 让真实买家说出关键短语 |
| Q&A 区里被高赞过的回答 | 主动引导买家在 Q&A 里答 |
| 跟问题语义匹配的描述 | description 里写得明白 |
| 没有 negative pattern | review 中没有反复出现的 deal-breaker |

**对服装的影响**:买家问 Rufus "什么连衣裙适合 5'2 nightlife",Rufus 会:

1. 先看哪些产品 review/Q&A 里有人说自己 5'2 穿得好看
2. 再看 Listing 文案有没有"petite friendly""nightlife"这些词
3. 再看 review 里有没有"perfect for going out""club"

Rufus 给的不是关键词匹配,是"哪些产品的内容能让我说出一个有依据的回答"。

## 三算法对齐表(每个 Listing 元素给三家分别评分)

这张表每次产出修改建议时,Claude 都要给每条改动标 A10/COSMO/Rufus 获益等级(高/中/低/无)。

### Title

| 写法 | A10 | COSMO | Rufus |
|---|---|---|---|
| 关键词堆砌(`Womens Summer Dress Casual Long Sleeve...`) | 高 | 低 | 低 |
| 关键词 + 1 个场景词(`Women's Long Sleeve Midi Dress for Work and Casual`) | 高 | 中 | 中 |
| 关键词 + 场景 + 人群(`Women's Long Sleeve Midi Dress for Petite Working Moms, Office to Brunch`) | 中-高 | 高 | 高 |

服装类目 title 不用全堆人群和场景,容易被砍。**建议格式**:`[Brand] [核心人群描述 1 词] [品类] [关键 fit/material 1-2 词] [场合 1 词]`,例如:`AAA Petite Women's Wrap Midi Dress, Stretch Knit, Office Brunch`。

### Bullet 5 条结构(服装专用)

| Bullet 位置 | 应该写什么 | A10 | COSMO | Rufus |
|---|---|---|---|---|
| Bullet 1 | 版型定位 + 核心差异化(为谁/什么场景) | 中 | 高 | 高 |
| Bullet 2 | 面料成分 + 克重 + 弹力百分比 | 中 | 中 | 高 |
| Bullet 3 | 尺码建议(模特身高、穿着尺码、是否偏大偏小) | 中 | 中 | 高 |
| Bullet 4 | 场合适配(列 3-5 个具体场景) | 中 | 高 | 高 |
| Bullet 5 | 洗护 + 售后/退换政策 | 低 | 低 | 高 |

每条 bullet 前 80 字符是 A10 可见区,关键词必须前置。

### 主图 7 张(服装类目最优配置)

| 图位 | 内容 | A10 | COSMO | Rufus |
|---|---|---|---|---|
| 图 1(主图) | 白底正面/45度,版型轮廓清晰,**禁止文字**(平台规则) | 高(CTR) | 中 | 低 |
| 图 2 | 上身效果(模特穿着,正面) | 高(CTR) | 中 | 低 |
| 图 3 | 上身效果(背面 + 侧面) | 中 | 中 | 低 |
| 图 4 | 面料近景 + 文字标注(成分%、克重、弹力%、是否衬里) | 中 | 中 | 高 |
| 图 5 | 尺码表 + 模特身高 + 穿着尺码 + 实测三围 | 高(CR) | 中 | 高 |
| 图 6 | 场景图(3-4 个使用场景拼图,带场景文字标签) | 中 | 高 | 高 |
| 图 7 | FAQ 图(把 review 高频疑问 + 答案做成图文) | 低 | 中 | 高 |

**为什么图 7 是 FAQ**:Rufus 引用 Listing 时把图文都当文本,FAQ 图里"机洗会缩水吗?— 不会,预缩处理"会被 Rufus 答出来。

### A+ 模块(7 模块标准结构,服装版)

| 模块 | 内容 | A10 | COSMO | Rufus |
|---|---|---|---|---|
| Module 1 — Brand Story | 品牌定位 + 目标人群 | 低 | 高 | 中 |
| Module 2 — 模特实穿场景 | 3-4 模特(不同身高/体型),不同场合 | 中 | 高 | 中 |
| Module 3 — 面料/工艺 | 面料近景 + 工艺细节 + 数据 | 中 | 中 | 高 |
| Module 4 — Size Guide | 详细尺码表 + How to Measure + 身高穿着对照 | 高 | 中 | 高 |
| Module 5 — Comparison Chart | 自家系列对比(避免提竞品名字) | 中 | 中 | 高 |
| Module 6 — FAQ | 5-8 条常见问 + 答 | 低 | 中 | 高(直接被引) |
| Module 7 — Care Guide | 图文洗护说明 | 低 | 低 | 高 |

### Q&A 区 + Review 引导

Rufus 极度依赖 review 语言,但你不能刷评。合规做法:

1. **售后卡 / 邮件**只**引导买家描述使用场景**,不暗示评分:
   - ❌"如果满意请给五星"
   - ✅"如果方便的话,可以分享一下你穿这件衣服去了什么场合、跟什么搭配,这能帮到其他买家做决定"

2. 这种引导会让真实买家说出"穿去 X 场合""配 Y 鞋"等场景化语言,Rufus 会把这些当成证据引用。

3. **Q&A 区**:亲友团 / 老客户被问到时,鼓励他们用具体数据回答(身高、体重、平时穿什么尺码、收到货实际怎么样),而不是"很好"。

## 算法对齐打分

每条修改建议输出时,Claude 必须给一个三栏对齐表:

| 修改 | A10 收益 | COSMO 收益 | Rufus 收益 | 总分 |
|---|---|---|---|---|
| 在图 4 加面料近景 + 200gsm 标注 | 中(转化) | 低 | 高(可被引) | 7/9 |
| Bullet 1 改成"Designed for petite working moms..." | 中 | 高(场景人群) | 高(具体描述) | 8/9 |
| A+ Module 6 加 FAQ"Will it shrink?— No, pre-shrunk" | 低 | 低 | 高 | 4/9 |

总分 ≥ 6/9 的优先做。

## "三家都不喜欢"的常见错误(必须修)

- title 全大写堆砌关键词 → A10 只是中等,COSMO/Rufus 都低,且现代主搜算法已经在惩罚 keyword stuffing
- bullet 写满营销语("BEST QUALITY EVER!""LIFETIME GUARANTEE!")→ A10 中,COSMO 低,Rufus 极低(无法被引用)
- 主图过度修图 → A10 短期 CTR 高,但退货率拉高,A10 会反向打,COSMO 不直接影响,Rufus 在 review 出现"different from photo"时会主动引用打你
- 没有尺码表图 → A10 间接受影响(退货高),COSMO 不直接影响,Rufus 直接吃亏

## 反向用 Rufus 验证算法对齐

**你做完修改后**,用 Rufus 重新跑这八题作为回测:

1. "Is this dress good for [你的目标场景]?"  ← 验 COSMO 场景
2. "Is this dress good for [你的目标人群]?"  ← 验 COSMO 人群
3. "What's the fabric of this dress?"  ← 验事实可被引(Rufus)
4. "Will this dress shrink?"  ← 验 FAQ 可被引(Rufus)
5. "Does this fit petite/plus/tall people?"  ← 验尺码描述
6. "How does this compare to [类似平价款]?"  ← 验对比表
7. "What do customers say about [你最担心的 complaint 维度]?"  ← 验 review 引导效果
8. "Best dress for [核心场景] under [价位]?"  ← 验有没有被推荐(终极指标)

第 8 题如果 Rufus 推到你 = 三家都对齐了。
