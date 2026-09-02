# 对话系统（Open WebUI + Ollama）

对话问答 + RAG 知识库，知音（ZhiYin）的子项目之一。Open WebUI 与 Ollama 以**原生进程**方式运行
（不依赖 Docker；`docker-compose.yml` 仅作为可选备选方案保留在仓库根目录）。

## 启动

双击 `启动.bat`（自动拉起 Ollama 和 Open WebUI，模型随 Ollama 加载）。启动前请确认：

- 已安装 Ollama（`%LOCALAPPDATA%\Programs\Ollama\ollama.exe`），并已拉取模型，见根目录 `DEPLOY.md`；
- 仓库根目录 `venv` 已创建并安装 open-webui（见 `DEPLOY.md`）；
- `loader.js` 已内联进 open-webui 前端（`python scripts\inline_loader.py`）。

首次启动请用浏览器打开 http://localhost:8088 **创建管理员账号并登录**（WEBUI_AUTH=True）。

## 使用

- 对话界面：http://localhost:8088 （登录后直接对话）
- Ollama API：http://localhost:11434
- OpenAI 兼容 API：http://localhost:11434/v1

## 关闭

双击 `关闭.bat`，或直接停止对应进程。

## 端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Open WebUI | 8088 | Web 对话界面 + RAG 前端 |
| Ollama | 11434 | 本地 LLM 推理（qwen2.5:7b + bge-m3） |

## 依赖与数据（仓库根目录共享）

- 运行时：`..\venv`（Open WebUI 环境）、`..\runtime`（ffmpeg 等，可选）
- 数据：`..\data\open-webui`（对话数据/记忆/知识库）、`..\data\ollama\models`（模型权重）
- 公共依赖说明：`..\共享资源\说明.md`

## loader.js 前端增强（本子项目自带）

对话页面的增强功能（模型记忆、系统定义生成🧠、数字人窗口🎭、朗读回退等）由根目录
`loader.js` 实现，需在安装 open-webui 后执行一次 `python scripts\inline_loader.py` 注入；
功能说明与常见问题见根目录《使用说明.md》。
