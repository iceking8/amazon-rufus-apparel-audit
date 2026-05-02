---
name: amazon-rufus-apparel-audit
description: 服装类目 Amazon 卖家专用——通过 Rufus 抓取竞品和自家 Listing 的买家问答,识别尺码/版型/面料/场合/洗护/差评/竞品对比七大维度的内容空缺,产出针对 A10/COSMO/Rufus 三算法对齐的中文优化方案,直接给到运营美工执行(改图N第N屏 / bullet N / A+ 模块N)。Trigger on:服装 Listing 优化、Rufus 竞品分析、服装 Q&A 抓取、A10 排名、COSMO 召回、Rufus 推荐、亚马逊算法对齐、服装转化率、尺码差评分析、apparel Listing audit。
---

# Amazon Rufus 服装 Listing 审计

## 这个 skill 解决什么问题

**给亚马逊服装卖家用**。把竞品 Rufus 暴露的买家担忧,翻译成你 Listing 上的具体修改动作,同时让修改方向能同时讨好 A10(关键词排名)、COSMO(语义召回)和 Rufus(AI 助手推荐)三个算法。

**不解决**:不操控 Rufus 输出、不刷评、不承诺排名结果。这里的逻辑是"内容覆盖度提升 → 转化率提升 → A10 反馈循环 + COSMO 意图匹配 + Rufus 引用素材"。

## 调用方四阶段流程

每次任务严格按四步走,不允许跳过:

1. **Profile 阶段**——读 Listing(自家 + 竞品)建产品档案
2. **Plan 阶段**——根据档案 + 服装六维生成提问计划
3. **Capture 阶段**——浏览器自动化 / 手动粘贴抓 Rufus 问答
4. **Report 阶段**——输出中文执行报告(图/A+/bullet/title 各改什么)

详细每阶段做什么、产出什么,看 [references/audit-workflow-apparel.md](references/audit-workflow-apparel.md)。

## 服装类目核心维度(必须覆盖)

每次 Q&A 抓取必须覆盖这七维,缺哪维要在报告里标注:

| 维度 | 典型买家问 | 决定 Listing 哪里改 |
|---|---|---|
| **尺码 (size)** | 我 165cm 60kg 穿 M 还是 L? | 尺码表图、A+ Size Guide 模块、bullet 尺码建议行 |
| **版型 (fit/silhouette)** | 这是宽松 oversize 还是修身? | 主图正面侧面背面、A+ 模特实穿、bullet 第 1 条版型定位 |
| **面料 (fabric)** | 是棉的还是化纤?会起球吗?夏天闷不闷? | 图4面料近景图、A+ 面料模块、bullet 面料行 |
| **场合 (occasion)** | 上班能穿吗?跑步出汗会透吗? | 场景图(图6/图7)、A+ 场景模块、bullet 场合行 |
| **洗护 (care)** | 机洗会缩吗?要熨烫吗? | 洗标图、A+ 洗护模块、bullet 洗护行 |
| **差评/退货 (complaint)** | 跟图色差大吗?到货褶皱? | 反向触发要解释的点,放在 FAQ 图 + A+ FAQ 模块 |
| **竞品对比 (vs competitor)** | 跟 X 牌比有什么区别? | A+ Comparison Chart、对比表(自家系列内对比) |

完整 taxonomy(细分类、优先级打分、覆盖标签)看 [references/apparel-question-taxonomy.md](references/apparel-question-taxonomy.md)。

## 算法对齐核心思路(这是这个 skill 的灵魂)

A10、COSMO、Rufus 不是三件事,是同一份 Listing 优化的三个反馈通道:

- **A10 看转化和点击** → 主图、价格、review 数量、search term 后台
- **COSMO 看语义/场景/人群** → Listing 文案有没有写"为谁、什么时候、解决什么"
- **Rufus 看可被引用的事实** → A+ 文案、bullet、Q&A、review 里有没有具体可引的句子

一条好的修改建议会同时打中三家。完整对齐表看 [references/algo-alignment.md](references/algo-alignment.md)。

## 输入要求

每次任务,问用户拿这些(缺哪个就标 `not_provided` 不要硬猜):

- 自家产品的 ASIN 或 URL(必需,role=`own`)
- 至少 1 个,推荐 3-5 个竞品 ASIN/URL(role=`competitor_1..N`)
- 站点(US/UK/DE/CA,默认 US)
- 子类目(连衣裙/T恤/外套/运动裤/泳装/内衣/童装 等,影响 question 模板)
- 目标人群标签(可选,如"25-35 通勤女性"、"健身爱好者"、"宝妈日常")
- 是否要自动化抓取还是手动粘贴 Q&A
- 期望抓取深度(默认每个 ASIN 收 15-25 条)

## 自动化抓取(可选)

VPS + Chrome + browser-harness 环境,一次配置长期复用:

- 首次环境配置:`scripts/setup_env.py`(可选,只在新 VPS 跑)
- 首次 Amazon 登录:`scripts/login_amazon.py`(凭据走环境变量,**不接受 stdin 输入**)
- 单次抓取:`scripts/capture_rufus.py --asin B0XXXX --depth 20`
- 报告生成:`scripts/build_report.py --capture out/capture.json`

详细自动化代码和 React-safe 注入模式看 [references/automation-patterns.md](references/automation-patterns.md) 和 [references/browser-capture.md](references/browser-capture.md)。

## 输出标准(中文,运营美工可执行)

每次任务最少产出:

1. **Capture Health 健康报告**——抓了多少条、多少有效、为什么有失败
2. **产品档案** ——自家+竞品逐个,product_type / 目标人群 / 版型描述 / 面料 / 场合 / 已知差评模式
3. **七维买家担忧地图**——每个维度竞品都被问到了什么,我家被问到了什么
4. **Listing 覆盖矩阵**——每个担忧我家是 强/部分/弱/缺失/被打脸
5. **优先级修复清单**——按 1-5 分排,5 分必改
6. **修改方案(分位置)**:
   - **主图 7 张**——第几张要改成什么、加什么文字标注
   - **A+ 模块**——第几模块要新增/改成什么内容
   - **Bullet 5 条**——逐条给出修改后文案
   - **Title**——给 1 个保守版 + 1 个激进版
   - **FAQ / 后台 search term**——直接给候选词
   - **Review 引导**——售后卡/邮件该引导买家说什么(合规框架内)
7. **算法对齐说明**——这次改动 A10/COSMO/Rufus 各自获益点
8. **回测计划**——3 个月、6 个月分别回查什么

完整 schema 和 CSV 表头看 [references/output-schema-cn.md](references/output-schema-cn.md)。
具体怎么改图、改 A+、改 bullet,看 [references/fix-playbook-apparel.md](references/fix-playbook-apparel.md)。

## 安全护栏(死规矩)

**绝对不能做**:

- 不允许用 Python `input()`、stdin 阻塞提示收凭据/验证码——后台 agent 跑批会直接 EOFError 崩
- 凭据/cookie/OTP/手机号/验证码不进 GitHub、不进 skill、不进 log、不进 CSV、不进截图
- 不绕 CAPTCHA、不绕账号安全验证——遇到就停下来通过 chat 通道问用户
- 不操控 Rufus 输出、不承诺排名上升、不写"100% 成功率"这种话
- 不修改买家账号的 profile / 地址 / 支付 / 评价 / 消息

**遇到这些情况立刻停**:

- 浏览器没登录 Amazon 买家账号 → 标 `login_status=not_logged_in`,通过 chat 问用户登录方式,**绝不用 input()**
- Amazon 弹"Add a mobile number" → 标 `challenge_type=mobile_number_required`,问用户手机号,提交后回复"已添加手机号",再问短信码
- 出 CAPTCHA / robot check / 账号安全警告 → 直接停,不试自动绕

完整安全规则:[references/account-safety.md](references/account-safety.md)。

## 抓取健康闸门(必经)

任何分析输出之前必须先通过这一关:

- 失败行(`question_only` / `blocked` / `out_of_scope`)占比 > 30% 时,报告头一段就要写明,不允许把不可信数据当结论
- 自家 Listing 没拿到时,只能出"竞品担忧地图",不能出"我家有 N 个 gap"
- 同一个会话里产品 ID 漂移(点着点着答的是别的产品)的行,标 `out_of_scope` 排除

## Reference 索引

| 文件 | 用途 |
|---|---|
| [references/audit-workflow-apparel.md](references/audit-workflow-apparel.md) | 四阶段详细流程 |
| [references/apparel-question-taxonomy.md](references/apparel-question-taxonomy.md) | 服装七维 question 体系、优先级打分 |
| [references/product-profiling-apparel.md](references/product-profiling-apparel.md) | 服装专属产品档案 schema |
| [references/algo-alignment.md](references/algo-alignment.md) | A10 / COSMO / Rufus 三算法对齐指南 |
| [references/fix-playbook-apparel.md](references/fix-playbook-apparel.md) | 主图/A+/bullet/title 服装版怎么改的具体剧本 |
| [references/output-schema-cn.md](references/output-schema-cn.md) | 中文输出表 schema、CSV 表头、报告结构 |
| [references/browser-capture.md](references/browser-capture.md) | 浏览器自动化护栏(状态机、稳定性判定) |
| [references/automation-patterns.md](references/automation-patterns.md) | React-safe 注入、CDP 登录、批量循环代码 |
| [references/account-safety.md](references/account-safety.md) | 凭据/OTP/手机号/CAPTCHA 处理规则 |
| [references/troubleshooting.md](references/troubleshooting.md) | 常见抓取失败模式与对应失败码 |

## Scripts 索引

| 文件 | 用途 |
|---|---|
| `scripts/setup_env.py` | 一次性环境安装(Chrome + Xvfb + browser-harness),可选 |
| `scripts/login_amazon.py` | CDP WebSocket 登录,凭据走环境变量,session 持久化 |
| `scripts/capture_rufus.py` | 单 ASIN 抓取主程序,带状态机和失败行保留 |
| `scripts/build_report.py` | 读 capture JSON / CSV,出中文 Markdown 报告 |
