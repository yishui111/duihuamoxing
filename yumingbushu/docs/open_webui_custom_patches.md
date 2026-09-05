# Open WebUI 框架定制修改档案（FRAMEWORK PATCHES）

> 本文件记录对 Open WebUI（0.11.x）框架的定制修改，用于审计、回滚与升级维护，
> 内容指向兄弟项目 duihuamoxing 的 venv 内文件。
> **原则：全部为最小侵入修改，未改动框架架构与核心功能，均向后兼容。**

## 一、修改总览

| # | 文件 | 改动 | 影响范围 |
|---|---|---|---|
| 1 | `venv\Lib\site-packages\open_webui\env.py` | 去掉 WEBUI_NAME 自动追加的 " (Open WebUI)" 后缀；默认名「知音」 | 仅应用名显示 |
| 2 | `venv\Lib\site-packages\open_webui\models\users.py` | 新增 `get_user_by_username()` 方法 | 新增能力，不动原有方法 |
| 3 | `venv\Lib\site-packages\open_webui\models\auths.py` | `authenticate_user()` 支持用户名登录 | 认证：用户名/邮箱可登录 |
| 4 | `venv\Lib\site-packages\open_webui\frontend\index.html` | title 知音 + SW 注销脚本 + 悬浮（🧠/🎭）注入 + 登录守卫 + 微信风格用户页面 | 前端注入（不改原 UI 代码） |
| 5 | `venv\Lib\site-packages\open_webui\main.py` | ① 静态资源响应 no-cache；② `/api/v1/models` 注释 get_filtered_models | 缓存自愈；普通用户可见全部模型 |
| 6 | `venv\Lib\.env` | `WEBUI_AUTH=True` + `BYPASS_MODEL_ACCESS_CONTROL=true` | 开启认证；普通用户可调任意模型（官方开关） |

## 二、详细改动（含回滚方法）

### 1. env.py（备份：env.py.bak）

改前：
```python
WEBUI_NAME = os.getenv('WEBUI_NAME', 'Open WebUI')
if WEBUI_NAME != 'Open WebUI':
    WEBUI_NAME += ' (Open WebUI)'
```
改后：
```python
WEBUI_NAME = os.getenv('WEBUI_NAME', '知音')
```
回滚：用 `env.py.bak` 覆盖，或删除自定义默认值。

### 2. users.py（新增方法，无原始备份，改动如下）

在 `get_user_by_email()` 之后新增（未修改任何原有代码）：
```python
async def get_user_by_username(self, username, db=None):
    """Case-insensitive username lookup using SQL lower()."""
    async with get_async_db_context(db) as session:
        username_filter = func.lower(User.username) == username.lower()
        query = select(User).where(username_filter)
        match = (await session.execute(query)).scalars().first()
        if match is None:
            return
        return UserModel.model_validate(match)
    return
```
回滚：删除该方法即可（其余代码原样）。

### 3. auths.py（回滚：删除新增的两行，恢复 email-only 匹配）

`authenticate_user()` 中（用户名登录版）：
```python
resolved = await Users.get_user_by_username(email, db=db)
if not resolved:
    await verify_password(PLACEHOLDER_HASH)
    return
```
回滚：恢复原始 email-only 匹配：
```python
resolved = await Users.get_user_by_email(email, db=db)
if not resolved:
    await verify_password(PLACEHOLDER_HASH)
    return
```
说明：曾先改为「email 优先 + username 兜底」，随后按用户要求**彻底改为仅 username**
（邮箱登录关闭）。

### 4. D-Skwx6s.js（备份：D-Skwx6s.js.bak）

仅替换两处翻译 value（key 未动，不影响 i18n 查找）：
- `pt="电子邮箱"` → `pt="账号"`
- `"Enter Your Email":"输入您的电子邮箱"` → `"Enter Your Email":"请输入账号"`

### 5. index.html（备份：index.html.bak）

- `<title>Open WebUI</title>` → `<title>知音</title>`
- `</head>` 前增加 Service Worker 注销脚本（缓存自愈）
- **删除内联自动登录脚本 `__ragAutoAuth`**（原 432-457 行）：该脚本曾内置固定弱账号
  自动登录，认证开启后会反复请求导致 400/限流、卡登录页。已删除（弱口令原文不入库）

### 6. site-packages\.env（新增文件，删除即还原）

```
WEBUI_AUTH=True
```

## 三、未修改的部分（框架核心原样）

以下**完全没有改动**，保持 Open WebUI 官方原版：
- 数据库表结构（alembic 迁移、user/auth/chat 等表）
- API 路由结构（routers/*.py 除 auths.py 两行新增）
- WebSocket/实时通信（socket/）
- RAG 知识库管道（retrieval/、rag.* 配置）
- 记忆系统（memory 相关）
- 语音识别/合成（audio.*）
- 文件上传、共享、用户管理、权限系统
- 前端整体 UI/组件（仅语言包两处文案 + 标题）

## 四、升级注意事项（重要）

**升级 Open WebUI（pip install -U open-webui）会覆盖上述全部修改**，升级后需按本文件重新打补丁：
1. env.py 品牌后缀（如需保留「知音」）
2. users.py / auths.py 的 username 登录支持
3. 语言包登录文案
4. index.html 标题 + SW 脚本
5. site-packages\.env（通常不受 pip 升级影响，但建议检查）

建议：升级前备份 site-packages\open_webui 目录，升级后逐条对照本文件补丁。

## 五、项目侧配套修改（非框架，记录备查）

| 文件 | 改动 |
|---|---|
| `duihuamoxing\启动.bat` | WEBUI_AUTH=True、WEBUI_NAME=知音、TTS/数字人路径修复、日志重定向（log\）、-u 无缓冲 |
| `duihuamoxing\loader.js` | 删除固定账号自动登录段（安全隐患）；品牌注释清理 |
| `duihuamoxing\数字人\启动.bat` | 日志重定向 + -u |
| `duihuamoxing\文字驱动语音\启动.bat` | 日志重定向 + -u |
| `yumingbushu\silent_start_local.bat` | 静默拉起 + 日志重定向 |

> 安全说明：所有真实口令/账号从不写入本档案与仓库；管理员账号在 Open WebUI 页面内
> 自行注册与修改密码。
