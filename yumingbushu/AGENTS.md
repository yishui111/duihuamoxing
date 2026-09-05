# AGENTS.md（本目录约定简版）

本目录（yumingbushu）是 duihuamoxing 项目的 Cloudflare Tunnel 公网部署工作台
（知音 ZhiYin：登录网关 + 运维面板 + 隧道管理脚本）。

## 约定

1. 所有交付物：启动/停止脚本（ASCII、CRLF、无 BOM、`%~dp0`/`$PSScriptRoot` 相对定位）、
   README.md、DEPLOY.md、依赖锁定；脚本本身不写中文，需要调用 duihuamoxing 的中文名
   启动脚本时经 `find_entry.ps1` + `entry_names.json` 探测
2. 文档与交流使用简体中文
3. 部署完成后必须实测通过，验证记录写进 DEPLOY.md 第十二节
4. 敏感文件一律不入库：`login_gateway\config.json`、`cloudflared\`（含 tunnel-token.txt）、
   `login_gateway\.secret`、`backup\`、`*.log`、`.webui_secret_key`（.gitignore 已覆盖）
5. 改域名映射前先读 DEPLOY.md 第十节（修改域名映射）与 docs/cloudflare_setup_notes.md
6. 布局前提：本仓库必须与 duihuamoxing 同级放置（同一父目录），脚本用 `..\duihuamoxing` 相对定位
---
### 关键点（2026-09-02 上传整理补充）
- 角色：把兄弟项目 duihuamoxing(知音) 经 Cloudflare Tunnel 发布到公网 nas.905283.xyz；自研 登录网关 login_gateway:8091(反代8088) + 运维面板 ops_dashboard:8090(仅本机)
- 密钥类一律不入库且需自备：login_gateway\config.json(建 config.json.example→自行改名填强密码)、\.secret、\.webui_secret_key、cloudflared\cloudflared.exe + tunnel-token.txt
- stop_local_services_2.bat 按「探测关闭类入口(一键关闭全部/关闭)，找不到即报错」实现——勿改成会自动启动服务的版本
- 中文入口文件名由 find_entry.ps1 + entry_names.json 运行时解析（此两文件勿删）；4 个中文目录 bat = GBK+chcp936 属正常
- 域名可提及，隧道内部 ID/token/账号口令已全部打码删除；新机按 DEPLOY 实测后填写验证记录
