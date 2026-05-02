# 服装类目产品档案 (Product Profile)

每个 ASIN 在做 Rufus 抓取**之前**必须先读 Listing 建档案。这是必经闸门,不是可选分析步骤。读不到的字段标 `not_captured`,**不允许猜**。

## 服装专属档案字段(扩展自通用 schema)

| 字段 | 必填 | 说明 / 取值 |
|---|---|---|
| `profile_id` | 是 | 稳定 id,如 `OWN-PROFILE` / `C1-PROFILE` |
| `capture_date` | 是 | ISO 日期 |
| `marketplace` | 是 | US / UK / DE / CA |
| `product_role` | 是 | `own` / `competitor_1` / `competitor_2` |
| `asin` | 是 | unknown 则填 unknown |
| `product_url` | 是 | 完整 URL |
| `profile_status` | 是 | complete / partial / blocked |
| **服装基础属性** | | |
| `apparel_subcategory` | 是 | 连衣裙 / 上衣 / 裤装 / 外套 / 内衣 / 泳装 / 童装 / 运动服 / 配饰 |
| `gender_target` | 是 | women / men / unisex / kids / baby |
| `silhouette` | 是 | bodycon / fitted / regular / relaxed / oversize / a-line / wrap / shift / bias-cut |
| `length_category` | 条件必填 | mini / midi / maxi / knee-length / cropped / regular / long(连衣裙、半裙、外套必填) |
| `key_cut_features` | 是 | 列举,如 `[high-waisted, off-shoulder, drop-shoulder, V-neck, square-neck]` |
| **面料数据** | | |
| `fabric_composition` | 是 | 如 `95% Cotton, 5% Spandex`,缺失标 not_listed |
| `fabric_weight_gsm` | 否 | 克重(g/m²),Listing 写了才填 |
| `stretch_pct` | 否 | 弹力百分比或 4-way / 2-way / no stretch |
| `lined` | 是 | yes / no / partial / not_specified |
| `transparency` | 否 | opaque / semi-sheer / sheer / not_specified |
| **尺码体系** | | |
| `size_chart_present` | 是 | listing_image / aplus_module / both / none |
| `size_range` | 是 | 如 `XS-XXL` / `0-16` / `S-3XL` |
| `model_height_disclosed` | 是 | yes_with_size / yes_no_size / no |
| `runs_size_review_signal` | 否 | runs_small / runs_large / true_to_size / mixed_signal / not_enough_reviews |
| **场景/人群** | | |
| `stated_occasions` | 是 | 列出 Listing 文案明确写到的场合,如 `[work, brunch, vacation, wedding-guest]`,空填 `[]` |
| `stated_target_persona` | 否 | Listing 是否点名目标人群,如 `petite_women`、`working_moms`、`plus_size` |
| **洗护** | | |
| `wash_method` | 是 | machine / hand / dry-clean / not_specified |
| `shrinkage_claim` | 否 | pre-shrunk / minimal / not_addressed |
| **价格 + 评分** | | |
| `price` | 是 | 当前价 |
| `price_tier` | 是 | budget(<$25)/ mid(25-60)/ premium($60-150)/ luxury(>$150) — 服装类目按这个分 |
| `rating` | 是 | 当前星级 |
| `review_count` | 是 | 评价数 |
| `top_complaint_themes` | 是 | review 1-3 星 top 3 主题,如 `[runs_small, see_through, color_fade]`,没读到填 not_captured |
| **图片审计** | | |
| `image_count` | 是 | 总数 |
| `image_size_chart` | 是 | yes / no |
| `image_fabric_closeup` | 是 | yes / no |
| `image_scene_lifestyle` | 是 | yes(几张)/ no |
| `image_back_view` | 是 | yes / no |
| `image_faq` | 是 | yes / no |
| **A+ 审计** | | |
| `aplus_present` | 是 | yes / no |
| `aplus_modules_count` | 否 | 模块数 |
| `aplus_has_size_guide` | 是 | yes / no |
| `aplus_has_comparison` | 是 | yes / no(自家系列对比) |
| `aplus_has_faq` | 是 | yes / no |
| `aplus_has_care` | 是 | yes / no |
| **变体** | | |
| `color_variants` | 否 | 颜色数 |
| `size_variants_full` | 是 | 是否覆盖 XS-XXL 全尺码 / 含 plus / 含 petite / 含 tall |
| **评价信号(影响 Rufus)** | | |
| `review_language_themes` | 否 | review 里反复出现的短语,如 `["fits like a glove", "compliments everywhere"]` — 这些 Rufus 会引用 |
| `negative_signal_severity` | 是 | none / low / medium / high(基于 1-3 星比例 + 主题严重性) |
| **缺失证据** | | |
| `missing_listing_evidence` | 是 | 列出读不到但应该有的字段,如 `[fabric_weight, model_height, washing_instructions]` |
| `profile_sources` | 是 | title / bullets / images / aplus / specs / qa / reviews / screenshots / pasted_text |

## 必读的 Listing 区块(顺序)

按这个顺序读,缺哪个标哪个:

1. **基础信息**:title / brand / 价 / 星 / 评数 / 变体
2. **Bullets** 5 条
3. **Product Details / 规格**:面料、产地、尺码范围
4. **主图 7 张**:逐图记录是不是上身/尺码表/面料/场景/FAQ
5. **A+ 内容**:有几个模块、各模块在讲什么
6. **现有 Q&A 区**:卖家或买家已答的高赞问题
7. **Review themes**:看前 50 条 + 1-3 星里前 20 条,提主题

## 服装类目典型"missing_listing_evidence" 检查清单

如果以下每一项都缺,就是高风险 Listing(基本上 Rufus 给不出有利答案):

- [ ] 面料成分百分比
- [ ] 模特身高 + 穿着尺码
- [ ] 尺码表图
- [ ] 至少 1 张面料近景图
- [ ] 至少 1 张背面或侧面上身图
- [ ] 洗护说明
- [ ] 弹力 / 衬里说明
- [ ] 至少 2 个具体场景(不是泛泛的 casual)
- [ ] 目标人群描述(petite / tall / plus / 通勤 / 妈妈)
- [ ] 系列内对比表(如果你有多 SKU)

## profile 完成度门槛

- 上面 10 项 ≥ 8 项有 → `profile_status=complete`,可以做完整 gap 分析
- 5-7 项有 → `profile_status=partial`,可以做但报告里要标注 evidence 不全
- < 5 项有 → `profile_status=blocked`,只能列 Listing 改进起步建议,不做 Rufus gap 推断

## 服装类目 question 启发(基于 profile 自动生成)

读完 profile,自动按下面规则生成 `product_profile_generated` 类型问题:

| profile 信号 | 触发问题 |
|---|---|
| `silhouette=oversize` | "Is this true to size or does the oversized fit run big?" |
| `length_category=mini` | "How short is the mini dress on a 5'7\" person?" |
| `lined=no` 且 `transparency=not_specified` | "Is this dress see-through? Need to wear a slip?" |
| `model_height_disclosed=no` | "What's the model wearing in the photos?" |
| `size_chart_present=none` | "What are the actual measurements for size M?" |
| `top_complaint_themes` 包含 `runs_small` | "Should I size up?" |
| `top_complaint_themes` 包含 `color_fade` | "Does the color fade after washing?" |
| `aplus_has_size_guide=no` | "How do I know which size to order?" |
| `stated_occasions=[]`(没标场合) | "What occasions is this dress for?" |
| `stated_target_persona` 缺 | "Is this dress for petite or tall women?" |
| `aplus_has_comparison=no` 且自家有相似 SKU | "How is this different from [自家其他 SKU]?" |
| `wash_method=not_specified` | "Can I machine wash this?" |
| `fabric_weight_gsm=not_specified` | "Is this fabric thick or thin?" |

每个生成问题必须带 `profile_signal` 标注是哪条证据触发的。
