# -*- coding: utf-8 -*-
"""ZhiYin Login Gateway - a fresh, self-written login gate in front of Open WebUI.

Listens on 127.0.0.1:8291. Users must sign in with the configured account
(password from config.json). Once signed in (signed cookie), all HTTP and
WebSocket traffic is proxied to Open WebUI on 127.0.0.1:8088.

The login page here is written from scratch: no email validation, no
framework quirks - just a clean account + password form.
"""
import hashlib
import hmac
import json
import secrets
import time
from pathlib import Path

import httpx
import uvicorn
import websockets as _ws
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse

BASE = Path(__file__).parent
CONFIG_FILE = BASE / 'config.json'
COOKIE_NAME = 'zhiyin_session'
COOKIE_TTL = 60 * 60 * 24 * 7  # 7 days
BACKEND = 'http://127.0.0.1:8088'
BACKEND_WS = 'ws://127.0.0.1:8088'

# session signing secret (persisted so restarts keep sessions valid)
SECRET_FILE = BASE / '.secret'
if not SECRET_FILE.exists():
    SECRET_FILE.write_text(secrets.token_hex(32), encoding='utf-8')
SECRET = SECRET_FILE.read_text(encoding='utf-8').strip()

# Credentials come ONLY from config.json - never ship a hard-coded default.
# If config.json is missing or the password field is empty, fail loudly
# instead of falling back to any built-in default.
if not CONFIG_FILE.exists():
    raise SystemExit(
        '[FATAL] config.json not found next to main.py. '
        'Copy login_gateway/config.json.example to login_gateway/config.json '
        'and fill in a strong password before starting the gateway.'
    )

with open(CONFIG_FILE, 'r', encoding='utf-8') as fh:
    CONFIG = json.load(fh)
USERNAME = str(CONFIG.get('username') or '').strip() or 'admin'
pw = str(CONFIG.get('password') or '').strip()
if not pw:
    raise SystemExit(
        '[FATAL] "password" is empty in login_gateway/config.json. '
        'Set a strong password (see config.json.example) before starting the gateway.'
    )

app = FastAPI(title='ZhiYin Login Gateway', docs_url=None, redoc_url=None, openapi_url=None)


def sign(payload: str) -> str:
    return hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_session() -> str:
    exp = int(time.time()) + COOKIE_TTL
    payload = f'{exp}.{secrets.token_hex(8)}'
    return f'{payload}.{sign(payload)}'


def valid_session(tok: str | None) -> bool:
    if not tok:
        return False
    parts = tok.split('.')
    if len(parts) != 3:
        return False
    payload, sig = f'{parts[0]}.{parts[1]}', parts[2]
    if not hmac.compare_digest(sig, sign(payload)):
        return False
    try:
        return int(parts[0]) > int(time.time())
    except ValueError:
        return False


LOGIN_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>知音 · 登录</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:"Microsoft YaHei",system-ui,sans-serif; background:linear-gradient(135deg,#0f172a,#1e3a5f); min-height:100vh; display:flex; align-items:center; justify-content:center; }
  .box { background:#fff; border-radius:16px; padding:40px 36px; width:340px; box-shadow:0 20px 60px rgba(0,0,0,.35); }
  .logo { text-align:center; font-size:26px; font-weight:700; color:#1e293b; margin-bottom:6px; }
  .sub { text-align:center; color:#94a3b8; font-size:13px; margin-bottom:28px; }
  label { display:block; font-size:13px; color:#475569; margin:14px 0 6px; }
  input { width:100%; padding:11px 14px; border:1px solid #cbd5e1; border-radius:8px; font-size:15px; outline:none; }
  input:focus { border-color:#3b82f6; box-shadow:0 0 0 3px rgba(59,130,246,.15); }
  button { width:100%; margin-top:24px; padding:12px; background:#3b82f6; color:#fff; border:none; border-radius:8px; font-size:15px; cursor:pointer; }
  button:hover { background:#2563eb; }
  .err { color:#dc2626; font-size:13px; margin-top:12px; min-height:18px; text-align:center; }
</style>
</head>
<body>
  <div class="box">
    <div class="logo">知音</div>
    <div class="sub">请登录后使用</div>
    <form method="post" action="/login" autocomplete="off">
      <label for="u">账号</label>
      <input type="text" id="u" name="username" placeholder="请输入账号" autofocus>
      <label for="p">密码</label>
      <input type="password" id="p" name="password" placeholder="请输入密码">
      <button type="submit">登 录</button>
      <div class="err">{err}</div>
    </form>
  </div>
</body>
</html>"""


@app.get('/login', response_class=HTMLResponse)
def login_page(err: str = ''):
    return LOGIN_PAGE.replace('{err}', err)


@app.post('/login')
async def login_submit(request: Request):
    form = await request.form()
    u = (form.get('username') or '').strip()
    p = form.get('password') or ''
    if u == USERNAME and p == pw:
        resp = RedirectResponse('/', status_code=302)
        resp.set_cookie(COOKIE_NAME, make_session(), max_age=COOKIE_TTL,
                        httponly=True, samesite='lax')
        return resp
    return HTMLResponse(LOGIN_PAGE.replace('{err}', '账号或密码错误，请重试'), status_code=401)


@app.get('/logout')
def logout():
    resp = RedirectResponse('/login', status_code=302)
    resp.delete_cookie(COOKIE_NAME)
    return resp


def check_session(request: Request):
    tok = request.cookies.get(COOKIE_NAME)
    if not valid_session(tok):
        raise HTTPException(302)  # will be caught below -> redirect


@app.api_route('/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
async def proxy(request: Request, path: str):
    tok = request.cookies.get(COOKIE_NAME)
    if not valid_session(tok):
        return RedirectResponse('/login', status_code=302)

    url = f'{BACKEND}/{path}'
    if request.url.query:
        url += '?' + request.url.query

    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in ('host', 'content-length', 'connection', 'accept-encoding')}
    body = await request.body()

    client = httpx.AsyncClient(timeout=None, trust_env=False)
    try:
        req = client.build_request(request.method, url, headers=headers, content=body)
        resp = await client.send(req, stream=True)
        out_headers = {k: v for k, v in resp.headers.items()
                       if k.lower() not in ('content-length', 'transfer-encoding',
                                            'content-encoding', 'connection')}

        async def gen():
            try:
                async for chunk in resp.aiter_bytes():
                    yield chunk
            finally:
                await resp.aclose()
                await client.aclose()

        return StreamingResponse(gen(), status_code=resp.status_code, headers=out_headers)
    except Exception as e:
        import traceback
        traceback.print_exc()
        await client.aclose()
        return Response(f'backend unavailable: {e}', status_code=502)


@app.websocket('/ws/{path:path}')
async def ws_proxy(websocket, path: str):
    tok = websocket.cookies.get(COOKIE_NAME)
    if not valid_session(tok):
        await websocket.close(code=1008)
        return
    try:
        await websocket.accept()
    except Exception:
        return

    query = websocket.scope.get('query_string', b'').decode()
    url = f'{BACKEND_WS}/ws/{path}'
    if query:
        url += '?' + query

    try:
        async with websockets_connect(url) as backend:
            async def client_to_backend():
                try:
                    while True:
                        msg = await websocket.receive_text()
                        await backend.send(msg)
                except Exception:
                    pass

            async def backend_to_client():
                try:
                    while True:
                        msg = await backend.recv()
                        if isinstance(msg, bytes):
                            await websocket.send_bytes(msg)
                        else:
                            await websocket.send_text(msg)
                except Exception:
                    pass

            import asyncio
            await asyncio.gather(client_to_backend(), backend_to_client())
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass


async def websockets_connect(url):
    return await _ws.connect(url, subprotocols=['socket.io'])


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8291)
