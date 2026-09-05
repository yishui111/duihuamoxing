
## 🚀 换电脑部署（保证可用）

> **方式 A（推荐 · 100% 保证）**：用 U 盘 / 网盘把「原项目整份文件夹」（含全部大件）复制到新电脑 → 双击 `start.bat` 即可。
>
> **方式 B（代码装配）**：`git clone` 本仓库 → 双击 `assemble.bat` 预检大件 → 按提示补齐缺失项（下载地址见下文/README）→ 双击 `start.bat`。

> 说明：引擎、模型、镜像、运行时等大件体积超过 GitHub 单文件 100MB 上限，**不随仓库分发**；本仓库承载全部自研代码与装配指引，"方式 A"是换机部署最稳路径，"方式 B"适合需要重新下载大件的场景。
# 知音（ZhiYin）· 部署方案（DEPLOY）

> 目标：在一台**新电脑**上，用本仓库把「知音」内容系统（duihuamoxing）通过
> Cloudflare Tunnel 发布到公网 **https://nas.905283.xyz** —— 无公网 IP、无端口映射。
> 本仓库只含源码/脚本/文档；运行期大件与敏感文件按下文准备。

## 0. 架构总览

```
外网用户（手机流量等）
   │
   ▼
https://nas.905283.xyz            （域名 905283.xyz 托管在 Cloudflare 云端）
   │
   ▼
Cloudflare 边缘节点 ── Cloudflare Tunnel ──（连接器主动外连，无需公网 IP）
   │
   ▼
本机 cloudflared（Windows 服务，开机自启）
   │
   ▼
自研登录网关 login_gateway :8091   （公网入口第一道登录，口令在 config.json）
   │
   ▼
Open WebUI「知音」:8088            （内容系统，duihuamoxing）
   └─ Ollama :11434 / 数字人 :48620 / TTS :8061
```

三个互不绑定的部分：**域名**（云端，永不消失）、**隧道连接器 cloudflared**（传菜员）、
**本地服务 duihuamoxing**（厨师）。换机只换「传菜员 + 厨师」，域名与隧道映射在云端无需重配。

## 1. 环境要求

| 项目 | 要求 |
|---|---|
| 操作系统 | Windows 10 / 11 64 位 |
| 磁盘 | 内容系统约 30GB+，建议 SSD |
| 内存 / 显卡 | 由 duihuamoxing 决定（16GB 能跑，32GB + NVIDIA 独显 8GB 更流畅） |
| 网络 | 能上外网即可（**无需公网 IP**）；上行越高外网越快 |
| 兄弟项目 | **duihuamoxing**：含 venv Python、Open WebUI 8088、Ollama 11434、数字人 48620、TTS 8061（其 venv 同时供本仓库网关/面板复用） |
| cloudflared | 官方二进制（约 52MB），见第 3 步 |

## 2. 获取代码并放置

1. 拉取本仓库：`git clone https://github.com/yishui111/yumingbushu.git`
   （不会用 git 就从 GitHub 页面 Code → Download ZIP 解压，效果一样）
2. **同级放置兄弟项目**（本仓库所有相对路径脚本都依赖这个布局）：

```
<父目录>\            ← 也可以是任意目录，两文件夹必须在同一父目录下
├── duihuamoxing\     ← 内容系统（复制自旧机器 / 备份介质，含 data\、venv\）
└── yumingbushu\      ← 本仓库
```

## 3. 运行期文件准备（不入库，新机器必做）

### 3.1 下载 cloudflared.exe

- 打开 https://github.com/cloudflare/cloudflared/releases
- 下载 `cloudflared-windows-amd64.exe`（约 52MB）
- 改名 `cloudflared.exe`，放入 `yumingbushu\cloudflared\`，最终为 `cloudflared\cloudflared.exe`

### 3.2 创建隧道 Token 文件（二选一）

**A. 已有隧道（换机迁移，推荐）**
1. 登录 https://dash.cloudflare.com → Zero Trust → Networks → Tunnels
2. 打开已有隧道（云端配置不动，换机无需重配域名映射）→ Configure
3. 复制 Token，新建 `yumingbushu\cloudflared\tunnel-token.txt` 并**粘贴内容（不要换行）**

**B. 全新隧道**
1. Tunnels → Create a tunnel → 命名（如 home-tunnel）
2. 复制生成的 Token → 同上存入 `tunnel-token.txt`
3. 进该隧道 → Public Hostname → Add：`nas` + 主域名 + HTTP + URL 填
   `localhost:8291`（公网入口先过登录网关；若你想直连 8088 用 Open WebUI 自带登录，则填 8088）
4. 保存，30 秒内生效

> ⚠️ `tunnel-token.txt` 相当于隧道钥匙，等于仓库里的 `cloudflared\` 已被 `.gitignore` 排除，请勿外发。

### 3.3 创建登录网关口令

```
copy login_gateway\config.json.example login_gateway\config.json
```

用记事本打开 `login_gateway\config.json`，把 `password` 改成你自己的强密码。
网关在 `config.json` 缺失或密码为空时会直接报错退出（不会使用任何默认口令）。
`config.json` 已被 `.gitignore` 排除，不会提交。

### 3.4 （可选）把隧道装成 Windows 服务（开机自启）

以**管理员**身份打开命令提示符，在 `yumingbushu\cloudflared\` 下执行：

```
cloudflared service install <tunnel-token.txt 里的内容>
```

验证：`sc query cloudflared` 显示 RUNNING；此后开机自动恢复隧道。
不装服务也可以，之后每次用 `start_cloudflared_2.bat`（没装服务时以前台窗口方式启动）。

## 4. 启动 / 停止（顺序口诀）

> **开 = 先开内容，再开通道；关 = 先关通道，再关内容。**

### 一键方式

| 动作 | 操作 |
|---|---|
| 一键上线 | 双击 `start.bat`（本地服务 → 登录网关 → 隧道；隧道步骤会弹 UAC，点「是」） |
| 一键下线 | 双击 `stop.bat`（隧道 → 登录网关 → 本地服务） |

### 分步方式（推荐新机器第一次用，便于观察每步结果）

| 顺序 | 上线 | 下线 |
|---|---|---|
| 1 | `start_local_services_1.bat`：启动本地服务，等 1-3 分钟模型加载，验证 http://localhost:8088 | `stop_cloudflared_1.bat`：先关外网通道 |
| 2 | `start_login_gateway.bat`：启动登录网关，验证 http://127.0.0.1:8291 | `stop_login_gateway.bat` |
| 3 | `start_cloudflared_2.bat`：启动隧道（UAC），自动打开公网域名 | `stop_local_services_2.bat`：最后关本地服务 |

> `start_local_services_1.bat` / `stop_local_services_2.bat` 会自动在 `..\duihuamoxing` 下
> 依次探测常见入口（start.bat / 一键启动全部.bat / 启动.bat，停止同理找 一键关闭全部.bat /
> 关闭.bat），找到即调用；一个都找不到时会提示（启动场景退回 `silent_start_local.bat`
> 拉起 Open WebUI + Ollama 基础服务，并提示数字人/TTS 需手动启动）。

### 停服对外网的影响

| 你停的东西 | 外网表现 | 恢复方法 |
|---|---|---|
| 只停本地服务 | 502 Bad Gateway | 重新 `start_local_services_1.bat` |
| 只停隧道 | 连接错误 / 隧道不可达 | `start_cloudflared_2.bat` 或 `net start cloudflared` |
| 全停 | 完全不可访问 | 先起内容（第 1 步）再起通道（最后一步） |

## 5. 端口 / 数据 / 日志 / 配置

| 项 | 值 |
|---|---|
| Open WebUI「知音」对话 | 8088（内容系统内部） |
| 登录网关（公网入口） | 8091（反向代理 8088） |
| 运维面板（仅本机） | 8090 |
| Ollama API | 11434 |
| 数字人素材服务 | 48620 |
| 内置朗读 TTS | 8061 |
| 对话数据 | `duihuamoxing\data\open-webui\webui.db`（迁移/备份必带） |
| 服务日志 | `duihuamoxing\log\`：webui / ollama / tts / avatar 各 .log + .err.log |
| 网关口令 | `login_gateway\config.json`（不入库，自行创建） |
| 会话密钥 | `login_gateway\.secret`（网关首次运行自动生成，不入库） |
| 隧道 Token | `cloudflared\tunnel-token.txt`（⚠️ 敏感，不入库） |
| cloudflared 日志 | Windows 事件查看器 → 应用程序日志（来源 cloudflared） |
| 诊断包 | `collect_logs.bat` → 仓库根目录 `diag_时间戳.zip`（不入库） |

## 6. 自动化（健康检查 / 备份 / 自启）

以管理员身份执行（把 `<父目录>` 换成 yumingbushu 实际的父目录路径，例如 `C:\apps`）：

```bat
:: 每 5 分钟体检：Open WebUI 挂了自动拉起（调用 silent_start_local.bat）
schtasks /Create /TN "ZhiYinHealthCheck" /TR "<父目录>\yumingbushu\auto_health_check.bat" /SC MINUTE /MO 5 /RL HIGHEST /F

:: 每天凌晨 3 点备份 webui.db 到 backup\（保留最新 7 份）
schtasks /Create /TN "ZhiYinBackup" /TR "<父目录>\yumingbushu\backup_webui.bat" /SC DAILY /ST 03:00 /F
```

- 隧道自启：见 3.4（cloudflared 服务 = Automatic）
- 也可手动：双击 `check_status.bat` 随时体检四服务 + 隧道 + 外网

> ⚠️ 手动/定时任务要等本地服务就绪后隧道才有内容可转发；电脑重启后若本地服务
> 未自动拉起，外网显示 502 属正常现象，健康检查任务几分钟内会自动拉起。

## 7. 验证（部署成功标准）

1. `sc query cloudflared` → RUNNING（若已装服务）
2. 本机 http://localhost:8088 能打开「知音」；http://127.0.0.1:8291 出现登录页
3. http://127.0.0.1:8290 运维面板：四服务 + 隧道全绿
4. **手机流量**（关 Wi-Fi）打开 https://nas.905283.xyz：先登录，后见「知音」，即成功

## 8. 常见问题排查

| 现象 | 原因与处理 |
|---|---|
| 外网 502 | 本地服务没起：本机打开 http://localhost:8088 验证，起服务后自动恢复 |
| 隧道 unhealthy / 连不上 | 网络或服务停了：`start_cloudflared_2.bat` 重启；确认能访问 github.com |
| 外网很慢 | Cloudflare 走国际节点，国内直连慢属正常；可自行搜索「Cloudflare 优选 IP」 |
| 提示 Token 失效 | token 与隧道绑定：重建/更新 `cloudflared\tunnel-token.txt` 后重装服务 |
| 网关报 FATAL config.json | 未创建网关口令：按 3.3 复制 config.json.example 并填强密码 |
| 脚本找不到 duihuamoxing | 布局不对：`duihuamoxing` 必须与本仓库同级（同一父目录） |
| 双击 start 脚本没反应 | 看是否弹了 UAC；确认 `cloudflared\cloudflared.exe` 已就位 |

## 9. 本机与目标机器可能不同的项

- **路径**：脚本全部用 `%~dp0` / `$PSScriptRoot` 相对定位，两文件夹放哪个父目录都行；
  但 cloudflared **装成服务后不能移动**（服务绑定绝对路径），要移动就重装一次服务
- **端口冲突**：8088 被占用时改 duihuamoxing 启动脚本里的 `--port`，并同步改云端
  隧道映射（见第 10 节）
- **无 GPU 机器**：TTS 自动降级 CPU（慢但可用），对话不受影响
- **凭据**：登录网关口令、Open WebUI 管理员口令、隧道 token 都是本机私有，换机重新设置

## 10. 修改域名映射（换子域名 / 换端口）

1. https://dash.cloudflare.com → Zero Trust → Networks → Tunnels → 你的隧道
2. Public Hostname → Edit：改子域名，或把 URL 从 `localhost:8291` 改成新目标
3. 保存后约 30 秒生效，**无需动本机**

## 11. 安全建议（强烈建议）

1. 登录网关是第一道登录；**Open WebUI 也建议开启自带登录**（duihuamoxing 启动脚本设
   `WEBUI_AUTH=True`），管理员账号在 Open WebUI 页面内注册/设置，口令自行保管
2. `login_gateway\config.json`、`cloudflared\tunnel-token.txt`、`login_gateway\.secret`
   均不入库、不外发；换机部署时通过 U 盘/加密渠道传递
3. 可选用 Cloudflare Zero Trust Access 给域名再加「邮箱验证码」访问策略（免费版需绑卡验证，不扣费）
4. 关闭 Open WebUI 外网自动注册；定期 `backup_webui.bat` 备份数据库

## 12. 部署验证记录（每次部署后填写）

| 检查项 | 结果 |
|---|---|
| cloudflared 服务状态 | RUNNING / 前台窗口 |
| 本机 8088 / 8091 / 8090 | 全部可访问 |
| 手机流量访问 https://nas.905283.xyz | 登录成功并进入「知音」 |
| 计划任务 ZhiYinHealthCheck / ZhiYinBackup | 已创建 / 已触发 |
| 健康检查自动拉起 | 停止 8088 后 5 分钟内自动恢复 |
| 备份恢复演练 | webui.db 备份可覆盖还原 |
