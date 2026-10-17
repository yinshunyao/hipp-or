# hipp-web

浏览器用户端，对齐 `hipp-uni` 的登录、话题、需求咨询、商业咨询与「我的」。接口复用 `hipp-api` 的 `/auth`、`/mp/chat` 与当前用户资料，不持有 Dify 密钥。

## 开发

先启动 `hipp-api`（默认 `http://127.0.0.1:46000`），再：

```shell
cd hipp-or/hipp-web
npm install
npm run dev
```

浏览器打开 `http://127.0.0.1:5173`。Vite 将 `/api` 反代到 46000 并去掉前缀，将 `/media` 原样反代。

## 构建

```shell
npm run build
```

产物在 `dist/`。线上请把站点与 `/api`、`/media`、WebSocket 升级头一起交给同一域名；接口前缀可用环境变量 `VITE_API_BASE`（默认 `/api`）。

## 页面

| 路径 | 说明 |
|:---|:---|
| `/` | 工作室首页 |
| `/login` | 短信登录 / 账号密码 |
| `/topics` | 归档话题；人工客服为接待列表 |
| `/chat/:id` | 会话（流式回复，失败回退同步发送） |
| `/requirement` | 需求咨询 |
| `/business` | 商业咨询 |
| `/mine` | 资料、密码、深色模式、关于 |
