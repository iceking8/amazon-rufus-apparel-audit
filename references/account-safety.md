# 账号安全规则

凡是涉及 Amazon 买家账号登录、OTP、手机号验证的步骤,严格按这一篇执行。

## 凭据存放规则

**绝不**把以下内容放进:GitHub、skill 文件、log、截图(对外分享的)、最终报告、CSV/JSON 输出、错误信息:

- 账号 / 邮箱 / 手机号
- 密码
- cookie / session token
- OTP/TOTP seed
- 一次性验证码(SMS code、邮件 code)
- 安全问题答案

**允许**的存放方式:

- 环境变量(`AMAZON_BUYER_EMAIL` / `AMAZON_BUYER_PASSWORD` / `AMAZON_BUYER_OTP_SECRET` / `AMAZON_BUYER_PHONE` / `AMAZON_BUYER_SMS_CODE`)
- 仓库外的 secrets 文件(明确 gitignore)
- agent 框架自带的 secret 通道(Anthropic / OpenAI 都有)

## 严禁 stdin / input() 的规矩

任何用 `input()` / `sys.stdin.readline()` / 阻塞 prompt 收凭据、OTP、手机号、短信码、确认覆盖文件等的代码,必须改成:

- 环境变量 / secret 文件读取
- 抛异常 → 上层通过 chat 通道问用户
- 非交互默认值

**为什么**:

- 后台 agent 跑批 stdin 关闭,直接 EOFError 崩
- stdin 输入易泄露(ps / strace / log)
- 多 ASIN 跑批中间阻塞等输入 = 整个任务废

## Pre-Authorized 登录流程

遇到登录或验证挑战时:

1. 检查用户是否已通过 secret 通道提供凭据
2. 如果有 → 用一次,只为本次登录
3. 如果 Amazon 要 OTP/TOTP → 检查是否提供了 OTP 工作流(本地 TOTP secret / 用户提供的验证服务 / human-supplied SMS)
4. 用完只在内存,**不写日志**,**不存盘**
5. 只在 capture 行里记非敏感的 `verification_action` 标签

如果 pre-auth 工作流失败:停下来,通过 chat 问人类协助,不要循环重试。

## 手机号验证完整流程(中文步骤)

Amazon 要求加手机号是它的高频反 bot 手段,服装类目尤其常见。

1. 检测到 "Add a mobile number" 页 → 立刻停 Rufus / Listing 抓取
2. 标 `challenge_type=mobile_number_required`、`failure_reason=mobile_number_verification_required`
3. 通过 chat 给用户消息:**"Amazon 要求添加手机号验证,请提供买家账号绑定的手机号(国际格式,如 +14155551234)"**
4. 用户回复后,程序填进表单提交
5. **填完立刻在内存丢弃手机号,不打印,不写 log**
6. 提交成功后,通过 chat 给用户**原文回复**:`已添加手机号`
7. Amazon 发短信码后,通过 chat 给用户消息:"请输入收到的短信验证码"
8. 用户回复后,填入验证码,**用完立刻丢弃**
9. 验证清除后回到 `login_state_check`,继续原任务

如果手机号或短信码被 Amazon 拒绝:不要循环重试,标 blocker 停止任务,告诉用户。

## Challenge 类型对照表

| `challenge_type` | 处理方式 |
|---|---|
| `login_required` | 用 pre-auth 凭据,失败问用户 |
| `otp_or_totp_required` | 用 TOTP 工作流,失败问用户 |
| `email_or_sms_code_required` | 走 pre-auth 检索,失败问用户 |
| `mobile_number_required` | 停下问用户手机号 → "已添加手机号" → 等短信码 |
| `mobile_number_code_required` | 问用户短信码,只用一次 |
| `captcha_or_robot_check` | **不绕**,停止任务,问用户人工介入 |
| `account_security_warning` | 停止,告诉用户去 Amazon 后台处理,不要继续抓取 |

## 允许写入 log / CSV 的非敏感字段

- `login_status=logged_in / not_logged_in`
- `verification_action=preauthorized_otp_used / human_phone_submitted / human_sms_code_submitted / human_intervention_needed`
- `challenge_type=login_required / otp_or_totp_required / mobile_number_required / mobile_number_code_required / captcha_or_robot_check / account_security_warning`
- `failure_reason=amazon_buyer_login_required / mobile_number_verification_required / no_preauthorized_verification_workflow`

## 账号使用范围

凭据**仅**用于:

- 用户授权的 Amazon 买家账号
- 前端 Rufus / Listing 浏览抓取

**不**用于:

- 修改账号 profile / 地址 / 支付
- 修改订单 / 评价 / 消息
- 任何写操作(下单、加购、收藏除外,如用户明确允许)
- 任何 persona 设置("Tell us about you" 等)——这会改变账号长期 Rufus 推荐行为,必须经用户单独 chat 确认

## 浏览器 profile 复用

`/tmp/chrome-profile` 这种持久化目录可以保留(用于免重复登录),但要:

- 不进 git
- 不打包到 zip 分发
- 退出任务时关闭浏览器进程,只保留目录
- 多任务复用同一目录时注意:cookie 共享意味着如果一个任务被风控,所有任务受影响
