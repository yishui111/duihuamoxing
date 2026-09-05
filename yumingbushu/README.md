<div align="center">

# 🌐 知音（ZhiYin）· Cloudflare Tunnel 公网部署工作台

> ⭐ **喜欢这个项目？请先点个 Star ⭐ 支持一下，让更多人看到！**

![GitHub stars](https://img.shields.io/github/stars/yishui111/yumingbushu.svg?style=flat-square&color=orange)
![GitHub forks](https://img.shields.io/github/forks/yishui111/yumingbushu.svg?style=flat-square)
![GitHub repo size](https://img.shields.io/github/repo-size/yishui111/yumingbushu.svg?style=flat-square)

**把本机「知音」对话系统（兄弟项目 duihuamoxing）通过 Cloudflare Tunnel 暴露到公网 https://nas.905283.xyz，并在入口加自研登录网关、配自研运维面板 —— 无公网 IP 也能安全上线。**

</div>

---

## ✨ 项目简介

本目录是 **duihuamoxing（知音 ZhiYin：Open WebUI 对话 + 知识库 + Ollama 大模型 + 数字人 + 朗读 TTS）的「公网部署工作台」**，已并入 duihuamoxing 仓库、作为其子目录 `yumingbushu/` 存在（原为同级兄弟仓库，2026-09-06 起合并）。负责三件事：

1. **开隧道**：用 Cloudflare Tunnel（连接器主动外连）把本机服务发布到公网 `https://nas.905283.xyz`，**不需要公网 IP、不需要路由器端口映射**；
2. **加登录**：入口前挡一层自研登录网关（`login_gateway`，8291，反向代理 Open WebUI 8088），账号密码放在不入库的 `config.json` 里；
3. **看状态**：自研运维面板（`ops_dashboard`，8290，仅本机访问），实时监控四个服务 + 隧道、查看日志、一键打包诊断。

换机器部署时，整个 `duihuamoxing` 文件夹拷走即可（本目录随仓库一起走），按 `DEPLOY.md` 准备 `cloudflared.exe`、隧道 token、网关口令即可，隧道配置（域名映射）在云端、换机无需重配。日常入口用仓库根目录的 **`公网上线.bat` / `公网下线.bat` / `公网状态.bat`**（分别调用本目录 `start.bat` / `stop.bat` / `check_status.bat`）。

> 适合场景：家里/办公室有一台装着大模型的 Windows 电脑，想随时随地用手机/外网访问它，又不想暴露公网 IP、不想被陌生人扫到。

## 🎯 主要功能

- 🔐 **自研登录网关**（`login_gateway/`，127.0.0.1:8291）：自绘登录页 + HMAC 签名会话 Cookie，登录后才转发 HTTP / WebSocket 到 Open WebUI（8088）；凭据只来自 `config.json`（不入库），缺配置即报错拒绝启动，**绝无内置默认口令**
- 🖥️ **自研运维面板**（`ops_dashboard/`，127.0.0.1:8290）：状态卡片（对话/Ollama/数字人/TTS + 隧道）、GPU 显存与磁盘进度条、进程内存列表、8 个日志在线查看、一键生成诊断包
- 🚇 **Cloudflare Tunnel 集成**：`start_cloudflared_2.bat` / `stop_cloudflared_1.bat` 管理隧道服务，支持开机自启（Windows 服务）
- ▶️ **成套启停脚本**：`start.bat`/`stop.bat` 总入口 + 分步 `start_local_services_1.bat` → `start_login_gateway.bat` → `start_cloudflared_2.bat`（口诀：**先内容后通道 / 先通道后内容**）
- 🩺 **健康检查与自动拉起**：`auto_health_check.bat`（配计划任务每 5 分钟体检，Open WebUI 挂了自动拉起）
- 💾 **自动备份**：`backup_webui.bat` 备份对话数据库到 `backup\`（保留最新 7 份，目录不入库）
- 📦 **一键报错诊断**：`collect_logs.bat` → 打包全部服务日志 + 系统信息成 `diag_时间戳.zip`

## 🗂️ 目录结构

```
duihuamoxing\yumingbushu\            ← 本目录（部署工作台，duihuamoxing 的子目录）
├── login_gateway/            # 自研登录网关（8291，反向代理 8088）
│   ├── main.py               # 网关代码（Python/FastAPI）
│   ├── config.json.example   # 配置模板：复制为 config.json 后填强密码
│   └── config.json           # （自建，不入库）网关账号口令
├── ops_dashboard/            # 自研运维面板（8290，仅本机）
│   ├── main.py
│   └── index.html
├── cloudflared/              # （自备，不入库）cloudflared.exe + tunnel-token.txt
├── docs/
│   ├── cloudflare_setup_notes.md      # Cloudflare 建隧道方法论笔记
│   └── open_webui_custom_patches.md   # Open WebUI 品牌/登录定制补丁记录
├── start.bat / stop.bat               # 一键上线 / 一键下线（总入口；仓库根的 公网上线/公网下线.bat 调用它们）
├── start_local_services_1.bat         # 第 1 步：启动本地服务（内容）
├── start_login_gateway.bat            # 启动登录网关
├── start_cloudflared_2.bat            # 第 2 步：启动隧道（通道，需管理员；服务起不来自动回退前台运行）
├── reinstall_cloudflared_service.bat  # （一次性，管理员）把 cloudflared Windows 服务重注册到本目录
├── stop_cloudflared_1.bat             # 第 1 步：停止隧道
├── stop_login_gateway.bat             # 停止登录网关
├── stop_local_services_2.bat          # 第 2 步：停止本地服务
├── silent_start_local.bat             # 静默拉起基础服务（供健康检查调用）
├── auto_health_check.bat              # 健康检查单次体检（配计划任务）
├── backup_webui.bat                   # 备份 webui.db（保留 7 份）
├── check_status.bat                   # 一键状态体检（四服务+隧道+外网）
├── collect_logs.bat / collect_diag.ps1# 一键收集诊断包
├── find_entry.ps1 / entry_names.json  # 定位父目录 duihuamoxing 的启动/停止入口（支持中文文件名，勿删）
├── .gitignore
├── AGENTS.md
├── README.md
└── DEPLOY.md
```

> 💡 本仓库只包含**源代码 / 脚本 / 配置模板 / 文档**。
> `cloudflared.exe`、`cloudflared\tunnel-token.txt`、`login_gateway\config.json`、
> 数据库备份、运行日志、`login_gateway\.secret` 等**敏感/运行期文件一律不入库**，
> 部署时按下方「配置」与「大件资源下载」自行准备。

## 🚀 快速开始（拉到新电脑即可部署）

### 环境要求

- 操作系统：Windows 10 / 11 64 位（脚本为 .bat/.ps1，本方案面向 Windows）
- 运行时：**父目录就是 duihuamoxing 本体**（内含 venv 版 Python、Open WebUI、Ollama、TTS、数字人，本目录网关/面板复用其 venv 里的 Python 与依赖）
- 网络：能上外网即可，**无需公网 IP**；域名 `905283.xyz` 托管在 Cloudflare（隧道映射在云端）

### 1. 布局（重要）

本目录已并入 duihuamoxing 仓库，必须作为其**子目录**存在：

```
duihuamoxing\              ← 项目根（对话/知识库/数字人/TTS 本体 + venv + data）
└── yumingbushu\           ← 本目录（部署工作台），脚本一律以父目录为项目根定位
```

### 2. 获取代码

```bash
git clone https://github.com/yishui111/duihuamoxing.git
cd duihuamoxing    # 工作台在 yumingbushu\ 子目录，随仓库一起到
```

### 3. 配置（三样东西，全部不入库）

1. **网关口令**：复制模板并填写强密码
   ```bash
   copy login_gateway\config.json.example login_gateway\config.json
   # 编辑 config.json，把 password 换成你自己的强密码
   ```
   > `login_gateway/main.py` 在 `config.json` 不存在或密码为空时会**直接报错退出**，不会退回任何默认口令。
2. **cloudflared.exe**：从 Cloudflare 官方 Releases 下载（约 52MB，见下节），放到 `cloudflared\cloudflared.exe`。
3. **隧道 token**：Cloudflare 控制台 → Zero Trust → Networks → Tunnels → 你的隧道 → Configure 复制 token，粘贴进 `cloudflared\tunnel-token.txt`（相当于隧道钥匙，勿外传）。

### 4. 启动（记住顺序口诀）

> **开 = 先开内容，再开通道；关 = 先关通道，再关内容。**

**一键上线**：双击 `start.bat`（= 本地服务 → 登录网关 → 隧道，隧道步骤会弹 UAC）。

或分步执行：

| 步骤 | 操作 | 说明 |
|---|---|---|
| 1 | 双击 `start_local_services_1.bat` | 启动本地服务（Open WebUI/Ollama/数字人/TTS），等 1-3 分钟模型加载 |
| 2 | 双击 `start_login_gateway.bat` | 启动登录网关（127.0.0.1:8291） |
| 3 | 双击 `start_cloudflared_2.bat` | 启动隧道（UAC 点「是」），自动打开 https://nas.905283.xyz |

**一键下线**：双击 `stop.bat`（= 隧道 → 登录网关 → 本地服务）。分步则先 `stop_cloudflared_1.bat` 再 `stop_login_gateway.bat` 再 `stop_local_services_2.bat`。

> 「本地服务」= 对话系统本体（相当于厨房）；隧道 = 大门。门开着厨房没火，外网会显示 502 —— 先确认 http://localhost:8088 能打开，再查隧道。

### 5. 验证

- 本机浏览器打开 http://localhost:8088（Open WebUI）与 http://127.0.0.1:8291（登录网关登录页）
- 运维面板 http://127.0.0.1:8290 四服务 + 隧道全绿
- **用手机流量**（关 Wi-Fi）打开 https://nas.905283.xyz → 先见登录页，登录后进入「知音」，即部署成功

## 📥 大件资源下载（运行期准备，不入库）

| 资源 | 用途 | 下载地址 / 获取方式 |
| ---- | ---- | ---- |
| cloudflared.exe（约 52MB） | Cloudflare 隧道连接器 | https://github.com/cloudflare/cloudflared/releases （windows-amd64.exe，改名 `cloudflared.exe` 放入 `cloudflared\`） |
| 隧道 Token | 连接你账号下的隧道 | Cloudflare 控制台 → Zero Trust → Networks → Tunnels → Configure → 复制 Token → 存入 `cloudflared\tunnel-token.txt` |
| 系统本体 duihuamoxing（几十 GB 大件） | Open WebUI 8088 / Ollama 11434 / 数字人 48620 / TTS 8061 | 本目录的父目录即是；大件按 duihuamoxing 的 DEPLOY.md 准备 |

## 🛠️ 本地开发 & 提交

```bash
git add .
git commit -m "feat: xxx"
git push origin main
```

- 网关/面板是标准 FastAPI 应用：`python -m uvicorn main:app --host 127.0.0.1 --port 8291 --app-dir login_gateway`（8290 同理）
- 依赖：`fastapi`、`uvicorn`、`httpx`、`websockets`（通常由 duihuamoxing 的 venv 提供）

## ❓ 常见问题（FAQ）

- **Q：外网 502 / 打不开？** A：先看本机 http://localhost:8088 是否正常（本地服务没起则 502）；再 `sc query cloudflared` 看隧道是否 RUNNING；最后 `collect_logs.bat` 打包日志排查。
- **Q：start_cloudflared_2.bat 报 cloudflared.exe / token 找不到？** A：按上文「配置」第 2、3 步准备 `cloudflared\cloudflared.exe` 与 `cloudflared\tunnel-token.txt`，它们不入库，新机器要自己放。
- **Q：登录网关启动报 FATAL config.json？** A：复制 `login_gateway\config.json.example` 为 `login_gateway\config.json` 并填写强密码 —— 网关刻意不允许空密码/默认密码。
- **Q：脚本报错说找不到 duihuamoxing / project root？** A：本目录必须位于 `duihuamoxing\yumingbushu\`（父目录即项目根）；整个文件夹被移出项目外就会找不到。
- **Q：删掉旧的同级 yumingbushu 文件夹前要做什么？** A：先以管理员身份运行一次 `reinstall_cloudflared_service.bat`，把 cloudflared Windows 服务的二进制路径从旧位置重注册到本目录；不重跑也能用（`start_cloudflared_2.bat` 会回退为前台进程运行隧道），但会失去"开机自启"。
- **Q：电脑重启后？** A：隧道是 Windows 服务（Automatic）会自动恢复；本地服务可由计划任务（ZhiYinHealthCheck）几分钟内自动拉起，详见 DEPLOY.md。

## ⚠️ 注意事项

- 敏感信息一律不入库（已写进 `.gitignore`）：`login_gateway\config.json`、`cloudflared\`（含 token）、`login_gateway\.secret`、`backup\`、`*.log`、`.webui_secret_key`；
- Open WebUI 侧建议开启自带登录认证（`WEBUI_AUTH=True`）作为第二道防线，管理员口令请在页面里自行设置，**本仓库不含任何账号口令**；
- 国内直连 Cloudflare 走国际节点，速度一般属正常现象；
- 本仓库仅供学习交流使用。

## 📄 许可证

MIT License

## 🙏 支持与致谢

如果这个项目帮到了你，**请点亮右上角的 ⭐ Star**，你的支持是我持续更新的最大动力！
