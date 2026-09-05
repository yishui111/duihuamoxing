# Cloudflare Tunnel 建隧道方法论笔记（从零到上线，无公网 IP 版）

> 本文是历史部署笔记的整理版（原「部署方案」），保留可复用的方法论；
> 完整的新机器操作以仓库根目录 **DEPLOY.md** 为准，本文作为概念与排查参考。
> 文中所有真实 Token / 隧道内部 ID 均已去除，一律以 `<占位>` 表示。

## 一、核心逻辑与解耦原则

家庭宽带通常没有公网 IP、运营商不给端口映射，传统「光猫端口映射」行不通。
Cloudflare Tunnel 的思路是：**让家里的电脑主动向外网发起连接**，打通一条专用通道。

三个东西互相独立：

- **域名（如 905283.xyz）** = 招牌，挂在云端，永不消失
- **隧道连接器 cloudflared** = 传菜员，负责把外网请求转到你电脑的指定端口
- **本地服务（如 duihuamoxing，8088/8091 等）** = 厨师，处理请求返回网页

换电脑完全不影响：新机器上重新放好 cloudflared.exe + 同一个 Token，隧道自动接上，
域名绑定（Public Hostname 映射）在云端，无需重配。

## 二、模块一：购买域名与 DNS 托管

1. 在域名注册商（如 Spaceship）购买一个域名，例如 `xxx.xyz`
2. 注册 Cloudflare 账号并添加该域名（Add a site）
3. 按 Cloudflare 提示，把域名的 Nameserver 改成 Cloudflare 分配的两个（控制台会显示）
4. 等待状态变为 Active（域名受 Cloudflare 保护），即可开始部署隧道

## 三、模块二：本地服务准备与自测

先让本机服务跑起来并能被本机访问，再谈暴露公网：

1. 确认/安装 Python（安装时勾选 Add Python to PATH）
2. 启动服务（本项目为 duihuamoxing，双击其启动脚本即可；临时验证可用
   `python -m http.server 8080`）
3. 浏览器访问 http://localhost:8080（本项目是 8088）能看到内容 = 服务本体 OK
4. 可选：在路由器后台给这台电脑做 DHCP 静态保留，固定内网 IP
   （本项目 cloudflared 为主动外连 + Windows 服务，固定 IP 非必需）

> 自测通过标准：本机能打开服务页面。服务窗口不能关，关了外网会 502。

## 四、模块三：部署隧道连接器

原生版（本项目采用，非 Docker）：

1. 下载 cloudflared.exe：https://github.com/cloudflare/cloudflared/releases
   （windows-amd64 版，改名 cloudflared.exe，放入 `cloudflared\`）
2. 登录 Cloudflare 控制台 → Zero Trust → Networks → Tunnels
3. **已有隧道**：打开隧道 → Configure → 复制 Token → 存入 `cloudflared\tunnel-token.txt`
   **新建隧道**：Create a tunnel → 命名（如 home-tunnel）→ 复制生成的 Token 存入 token 文件
4. 管理员命令行执行 `cloudflared service install <Token>` 装成 Windows 服务（开机自启），
   或双击仓库里的 `start_cloudflared_2.bat`（未装服务时以前台窗口方式运行）
   - 加 `--protocol quic` 可提升抗丢包能力，对国内网络更友好（装服务时的参数可自行调整）

> 自测通过标准：Cloudflare Tunnels 页面该隧道状态为 HEALTHY（绿色）。
> 提示 Token 失效 = Token 与隧道绑定，重建隧道后需更新 token 文件并重装服务。

## 五、模块四：绑定域名映射

在隧道页面 → Public Hostname → Add a public hostname：

- Subdomain：喜欢的名字，如 `nas`
- Domain：选你的主域名（如 905283.xyz）
- Type：HTTP
- URL：目标地址。本项目公网入口走**登录网关**填 `localhost:8291`；
  若要直连内容系统则填 `localhost:8088`（此时建议开启 Open WebUI 自带登录）
- 保存后约 30 秒生效

> 自测通过标准：**关掉 Wi-Fi，用手机流量**（4G/5G）访问 https://nas.905283.xyz，
> 看到与本地一致的内容（本方案为登录页 → 登录后进入「知音」）。
> 打不开先查本地服务是否还在运行。

## 六、模块五：性能优化与安全加固

1. **（可选）国内访问加速**：Cloudflare 默认走国际节点，国内直连较慢属正常；
   可搜索「Cloudflare 优选 IP」工具自行优化，普通个人使用可暂不处理
2. **（强烈推荐）加一道登录**：本仓库用自研 `login_gateway`（8091，公网入口登录，
   口令在不入库的 `login_gateway\config.json`）；内容系统内 Open WebUI 建议再开
   自带登录认证（WEBUI_AUTH=True）
3. **（可选）Cloudflare Zero Trust Access**：Zero Trust → Access → Applications 给域名
   加「邮箱验证码 / 允许的邮箱」策略，只有你能过（免费版需绑卡验证，不扣费）
4. 数据库定期备份（`backup_webui.bat`），日志用 `collect_logs.bat` 打包排查

## 七、最终联调顺序

不要跳步，每一步都有独立自测标准：

1. 模块二：本机服务可访问
2. 模块三：隧道 HEALTHY
3. 模块四：手机流量能打开域名并看到内容/登录页
4. 模块五：登录与加固生效

> 原文档中的「部署结果记录」含真实隧道内部 ID 与 DNS CNAME 详情，涉及账号信息，
> 已从公开仓库移除；如需查看，在 Cloudflare 控制台 Tunnels 页面可直接看到全部信息。
