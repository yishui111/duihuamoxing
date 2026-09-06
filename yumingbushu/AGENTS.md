# AGENTS.md（本目录约定简版）

本目录（yumingbushu）是 duihuamoxing 项目（父目录）的 Cloudflare Tunnel 公网部署工作台
（知音 ZhiYin：登录网关 + 运维面板 + 隧道管理脚本）。2026-09-06 起由同级兄弟仓库并入为子目录。

## 约定

1. 所有交付物：启动/停止脚本（ASCII、CRLF、无 BOM、`%~dp0`/`$PSScriptRoot` 相对定位）、
   README.md、DEPLOY.md、依赖锁定；脚本本身不写中文，需要调用 duihuamoxing 的中文名
   启动脚本时经 `find_entry.ps1` + `entry_names.json` 探测
2. 文档与交流使用简体中文
3. 部署完成后必须实测通过，验证记录写进 DEPLOY.md 第十二节
4. 敏感文件一律不入库：`login_gateway\config.json`、`cloudflared\`（含 tunnel-token.txt）、
   `login_gateway\.secret`、`backup\`、`*.log`、`.webui_secret_key`（.gitignore 已覆盖）
5. 改域名映射前先读 DEPLOY.md 第十节（修改域名映射）与 docs/cloudflare_setup_notes.md
6. 布局前提：本目录是 duihuamoxing 的**子目录**，脚本用 `%~dp0..` 解析出项目根（父目录）；
   不要把本目录移出 duihuamoxing 之外
---
### 关键点（2026-09-02 上传整理补充）
- 角色：把内容系统 duihuamoxing(知音) 经 Cloudflare Tunnel 发布到公网 nas.905283.xyz；自研 登录网关 login_gateway + 运维面板 ops_dashboard:8290(仅本机)。端口沿革：8091/8090 → 8291/8290（2026-09-06）→ **网关 8088 / WebUI 8089**（2026-09-07 最终态，网关占据云端映射的 localhost:8088，云端配置零改动即生效）
- 密钥类一律不入库且需自备：login_gateway\config.json(建 config.json.example→自行改名填强密码)、\.secret、cloudflared\cloudflared.exe + tunnel-token.txt
- stop_local_services_2.bat 按「探测关闭类入口(一键关闭全部/关闭)，找不到即报错」实现——勿改成会自动启动服务的版本
- 中文入口文件名由 find_entry.ps1 + entry_names.json 运行时解析（此两文件勿删）；4 个中文目录 bat = GBK+chcp936 属正常
- 域名可提及，隧道内部 ID/token/账号口令已全部打码删除；新机按 DEPLOY 实测后填写验证记录
### 关键点（2026-09-06 并入 duihuamoxing 后）
- 所有 `..\duihuamoxing` 引用改为 `%~dp0..`（cmd `for %%I in ("%~dp0..") do set "PROJECT=%%~fI"` 标准写法解析绝对路径）；ops_dashboard/main.py 的 ROOT = REPO_DIR.parent
- 日常入口用仓库根目录 公网上线.bat / 公网下线.bat / 公网状态.bat（调用本目录 start/stop/check_status）
- 删除旧同级目录前先管理员运行 reinstall_cloudflared_service.bat 重注册 cloudflared 服务（旧服务二进制路径钉在旧位置）；start_cloudflared_2.bat 已有"服务起不来→本目录前台运行"回退
- silent_start_local.bat 启动 Open WebUI 已固定 -WorkingDirectory 项目根（否则第二把 .webui_secret_key 会顶掉登录态），并补齐 OLLAMA_MODELS/KEEP_ALIVE 等与根启动脚本一致的环境变量
- 8290 端口可能被用户另一项目 chat_workbench.py 占用，面板起不来先查它
