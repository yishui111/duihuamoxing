# 文字驱动语音服务（GPT-SoVITS TTS）

输入文字 → 用训练好的 GPT-SoVITS 音色模型合成语音（TTS），知音（ZhiYin）的子项目之一。
本目录提供**自研封装服务** `tts_service\tts_api.py`（FastAPI，OpenAI 兼容协议）；
GPT-SoVITS 推理引擎为第三方开源项目，需按根目录 `DEPLOY.md` 安装到 `gptsovits\GPT-SoVITS`（不在 Git 内）。

## 启动

双击 `启动.bat`（自动检测声音模型、按显存选择 cuda/cpu，首次加载模型约 1-3 分钟）。
启动前确认：`gptsovits\GPT-SoVITS` 引擎已就位、`tts_service\models\` 下已有至少一个完整角色模型。

## 使用

- **服务地址**：http://127.0.0.1:8061
- **健康检查**：http://127.0.0.1:8061/health
- **音色列表**：http://127.0.0.1:8061/v1/audio/voices（OpenAI 兼容）
- **合成接口**：`POST /v1/audio/speech`（OpenAI 兼容协议，供对话系统朗读用）

## 关闭

双击 `关闭.bat`（按仓库根 `data\tts.pid` 记录停止）。

## 端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 文字驱动语音 | 8061 | TTS 合成服务（GPT-SoVITS） |

## 目录结构

```
文字驱动语音\
├── tts_service\
│   ├── tts_api.py     主服务（自研，FastAPI + OpenAI 兼容端点）
│   ├── models\        声音模型目录（放进去即识别；仓库不含模型）
│   └── tmp\           临时文件/缓存（运行时生成）
├── gptsovits\GPT-SoVITS\   推理引擎（第三方，按 DEPLOY.md 安装，不在 Git 内）
├── 启动.bat / 关闭.bat
├── README.md
└── 模型放置与使用.md    ★ 模型怎么放、怎么用，看这个
```

## 配置（环境变量，全部可选；启动.bat 已设默认值）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TTS_API_PORT` | 8060 | 监听端口（本项目用 8061） |
| `GSV_ROOT` | `..\gptsovits\GPT-SoVITS` | GPT-SoVITS 引擎根目录 |
| `GSV_MODELS_DIR` | `tts_service\models` | 声音模型目录 |
| `TTS_DEVICE` | cuda | cuda / cpu（显存 <10GB 自动 cpu） |
| `TTS_DEFAULT_VOICE` | azhong | 启动预热的默认音色 |
| `TTS_SAMPLE_STEPS` | 64 | 采样步数（32 更快、偶发跳读） |
| `FFMPEG_PATH` | 空 | mp3 转码用（可选） |

## 依赖

- Python 3.12 + PyTorch 等（GPT-SoVITS 官方要求，安装在仓库根 `runtime\py312`，见 DEPLOY.md）
- GPT-SoVITS 引擎与其预训练基座（见 DEPLOY.md 下载表）
- 可选 ffmpeg（mp3 转码）

## 接入对话系统

对话系统（Open WebUI 8088）设置 → 音频 → 文本转语音，语音服务填
`http://127.0.0.1:8061/v1`、音色选本服务的训练角色，朗读回复即用该声音；
8061 未启动时 loader.js 会自动回退浏览器系统语音并提示。
