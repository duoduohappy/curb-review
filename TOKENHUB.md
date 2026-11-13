# 腾讯云 TokenHub 接入

已根据控制台提供的信息支持 HY-Vision-2.0-Instruct。

- 接口：`https://tokenhub.tencentmaas.com/v1/chat/completions`
- 模型：`hy-vision-2.0-instruct`（服务端固定，无其他模型回退）
- 认证：Bearer API Key，仅在服务端保存
- 图片：Base64 Data URI，随请求发给腾讯云

## Render 配置

1. 在腾讯云创建 API Key，名称可填 `curb-review-demo`。默认可能有全模型权限，可在密钥管理中限制权限到所需模型/服务。不要发送或提交密钥到聊天、GitHub、网页前端。
2. 在 Render 服务 → Environment 添加/修改：

| 环境变量 | 值 |
|---|---|
| AI_PROVIDER | `tokenhub` |
| TOKENHUB_API_KEY | 粘贴刚创建的真实密钥 |
| PUBLIC_DEMO | `1` |
| AI_DAILY_LIMIT | `40`（全站滚动24小时调用次数上限，含失败） |

3. 保存并重新部署，或等待 Blueprint 同步。原有服务请确认 AI_PROVIDER 已改成 tokenhub。新 render.yaml 默认选择腾讯云，但不会包含或创建任何密钥。
4. 页面出现“腾讯云接口已配置”仅表示环境变量非空；勾选图片传输授权，先上传一张不含敏感内容的测试图片验证真实调用。此前失败的任务可在详情中“重新排队”。

免费额度和计费由腾讯云账户控制，本程序不能查询或修改后付费状态。请保持本模型后付费关闭；如日后打开后付费，相同 API 请求可能产生账单，本程序的次数上限不等于免费额度保护。额度不足时显示失败，不切换提供商、不替你开启付费。Render 重启会重置临时调用计数。

客户只需要浏览器，密钥由站点维护者统一配置。已有12张示例不使用模型，结果为预设。新照片需等待模型分析，不能据此直接作违停认定。

截图中显示的100万Tokens是账户体验包状态，不换算成固定照片张数；图片尺寸、提示词和输出长度都会影响实际消耗。

官方图片接入说明：https://cloud.tencent.cn/document/product/1823/136956

验证范围：接口地址、Bearer认证、图片字节、模型名称和错误脱敏通过 mock 测试；未取得真实密钥，因此尚未运行真实腾讯云调用。
