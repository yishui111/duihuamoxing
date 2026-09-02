# 数字人素材服务（自研，纯 Python 标准库）

数字人（虚拟形象）素材库服务，知音（ZhiYin）的子项目之一。提供「说话视频 → 嘴型图库」的建库工具和数字人主页面；
对话系统页面的头部数字人小画面由它提供素材，朗读回复时用 TTS 声音能量驱动嘴型。

> 本服务为**自研实现**（`avatar_server.py`，纯 Python 标准库 HTTP 服务，约 20MB 内存，无 GPU 需求），
> 页面与核心模块在 `avatar_web\`、`avatar_core\`。

## 启动

双击 `启动.bat`（用仓库根 `..\venv` 的 python 运行；也可直接 `python avatar_server.py`，无需任何第三方包）。

## 使用

- **建库工具**：http://127.0.0.1:48620/web/preprocess.html
  （上传说话视频 → 一键生成嘴型图库 = 新增数字人，素材库生成在 `avatar_libs\`）
- **数字人主页**：http://127.0.0.1:48620/web/index.html
  （加载素材库、能量/嘴型配置、试听）
- **API**：http://127.0.0.1:48620/api/libs（素材库列表）

## 关闭

双击 `关闭.bat`。

## 端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 数字人服务 | 48620 | 素材库 + 建库 + 主页面 |

## 目录结构

```
数字人\
├── avatar_server.py     主服务（纯 Python 标准库，环境变量可覆盖配置）
├── avatar_core\         页面引用的核心模块（嘴型/表情/特征映射，.mjs）
├── avatar_web\          前端页面（index.html / preprocess.html）
├── avatar_libs\         素材库（运行时由建库工具生成，仓库不含真人素材）
├── avatar_input\        建库视频暂存（运行时生成）
├── 启动.bat / 关闭.bat
└── README.md
```

## 配置（环境变量，全部可选）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `AVATAR_PORT` | 48620 | 监听端口 |
| `LIGHT_AVATAR_LIBS` | `avatar_libs`（本目录） | 素材库位置 |
| `FFMPEG_PATH` / `FFPROBE_PATH` | 空 | 视频转码用（可选；装了 ffmpeg 才会转码非 H.264 视频） |
| `AVATAR_LOG_DIR` | 仓库根 `data\logs` | 日志目录 |

## 依赖

- 运行时：任意 Python 3（标准库即可）；`..\venv`（若用 启动.bat）
- 可选：`..\runtime\ffmpeg`（建库视频转码）
- 安装与配置见根目录 `DEPLOY.md`

## 接入对话系统

对话系统（Open WebUI 8088）页面的数字人窗口指向本服务（48620），朗读时由 `loader.js`
拦截 TTS 音频计算能量曲线 → 驱动嘴型同步。
