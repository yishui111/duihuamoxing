# tests —— 功能验证脚本

本目录是部署后的功能验证脚本（需先按 DEPLOY.md 完成部署并启动服务）。

| 文件 | 作用 | 运行前提 |
|------|------|----------|
| `test_rag_chat.ps1` | 对话系统自检：Ollama 模型、bge-m3 嵌入、对话、Open WebUI 健康、登录/界面对话、语音端点 | Ollama + Open WebUI(8088) 已启动 |
| `loader_fetch_test.mjs` | 验证 loader.js fetch 包装 clone 修复（body stream already read） | Open WebUI 已启动 + 已注入 loader.js |
| `avatar_sync_test.js` | 数字人嘴型同步 e2e（采样嘴部像素验证嘴巴随声音动） | 对话系统+数字人已启动 + 本机 Chrome |

## 运行

```powershell
# Windows PowerShell（test_rag_chat.ps1 需要 UTF-8 BOM 已就绪）
powershell -ExecutionPolicy Bypass -File .\tests\test_rag_chat.ps1

# Node 测试（loader/avatar 需要登录账号；不提供则跳过）
$env:OWUI_EMAIL='user@example.com'; $env:OWUI_PASSWORD='<你的密码>'
node tests\loader_fetch_test.mjs
node tests\avatar_sync_test.js      # 另需 CHROME_PATH（默认自动探测 Chrome/Edge）
```

- `test_rag_chat.ps1` 前 4 项不依赖账号；第 5 项「登录+界面对话」在设置了
  `OWUI_EMAIL` / `OWUI_PASSWORD` 环境变量时才执行，否则 SKIP。
- 日志写入 `tests\output\`（已 gitignore）。

> 说明：早期开发期的其他测试脚本/临时产物未随仓库分发（可执行文件路径、本机账号等
> 敏感/机器相关信息不公开）。
