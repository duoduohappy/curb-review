# GitHub → Render 在线演示

本项目已适配 Render Web Service：监听 0.0.0.0:$PORT，自动加载模拟数据，支持 HTTPS 下的上传与复核。对方只需浏览器，无需安装 Python 或 Ollama。

## 1. 上传 GitHub

使用部署包时，将解压后的内容直接放在仓库根目录，确保根目录可见 `server.py`、`render.yaml`、`static/`、`samples/`。不要上传 data/、.env、API Key 或私人照片。

如果是空仓库，在本项目目录运行（将地址换成你的实际仓库）：

```sh
git init
git add .
git commit -m "Add Render-ready image evidence demo"
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPO.git
git push -u origin main
```

如果上传进已有仓库的子目录，Render 的 Root Directory 应填写该子目录；Blueprint 推荐把本项目置于根目录。

## 2. Render 创建服务

登录 https://dashboard.render.com/，选择 New → Blueprint，连接 GitHub 仓库。Render 会读取 render.yaml，创建免费 Python Web Service。创建前确认所选实例为 Free。

也可以 New → Web Service，手动填写：

| 设置 | 值 |
|---|---|
| Runtime | Python 3 |
| Build Command | `python -m compileall -q server.py` |
| Start Command | `python server.py` |
| Instance Type | Free |
| Health Check Path | `/healthz` |
| Environment | `AI_PROVIDER=openrouter`、`PUBLIC_DEMO=1`、`OPENROUTER_MODEL=openrouter/free`、`AI_DAILY_LIMIT=40` |

部署成功后，把 Render 给出的 https://你的服务.onrender.com 链接发给对方。没有 API Key 时，12 张预设样例的筛选、复核、导出仍可使用；上传新图则会显示模型未配置，不会伪造结果。

## 3. 开启免费云端视觉识别（可选）

在 https://openrouter.ai/ 注册并创建 API Key；在 Render 服务的 Environment 中添加：

`OPENROUTER_API_KEY=你自己的密钥`

不要将密钥放进 Git、网页 JavaScript 或截图。设置后保存并重新部署。页面将显示“免费云端接口已配置”，这只说明服务端有密钥，并不保证账户额度和当时的视觉模型可用。

默认 openrouter/free 根据带图片的请求选择可用免费模型。也可将 OPENROUTER_MODEL 改成平台当前支持图片输入的具体 `:free` 模型 ID。服务端拒绝付费模型名，同时把 prompt/completion 的 provider max_price 限制为 0；没有可用免费视觉模型、限流或 JSON 输出不合格时会明确失败，不转付费。账户免费额度与模型供应会变，不能保证长期稳定；无需为本演示主动充值。

访客上传前必须主动勾选同意将本批图片传给 OpenRouter 与其模型提供商。请用模拟图片或得到授权的测试照片。已有预设样例不调用外部接口。

每站滚动24小时最多40次模型调用（可用 AI_DAILY_LIMIT 调低）；每位访客最多20张真实上传记录；总图片存储上限200MB。调用次数含失败请求，重启会随临时数据库一起重置。这些是演示保护，不是抗滥用或完整账单系统。

## 演示版的数据边界

- PUBLIC_DEMO=1 使用 HttpOnly 随机会话 Cookie 区分访客，各自上传、复核与导出互相隔离。不是用户账号系统；清除 Cookie 后无法找回原会话。
- Render 免费服务空闲会休眠，首次打开可能需要等待启动。
- Render 免费实例文件系统是临时的：重启、休眠唤醒或重新部署后，上传图片及复核记录可能丢失；12张随源码打包的样例会重新加载。不要把它用作正式业务档案。重要结果请先导出。
- 页面轮询会在打开页面时产生访问；关闭网页后没有无人值守周度采集。
- 长期保存真实业务数据需另外接对象存储和数据库；这不是当前免费部署包的功能。

官方依据：[Render Free](https://render.com/docs/free)、[Web Services](https://render.com/docs/web-services)、[OpenRouter 免费路由](https://openrouter.ai/docs/guides/routing/routers/free-router)、[Provider 价格限制](https://openrouter.ai/docs/guides/routing/provider-selection)。
