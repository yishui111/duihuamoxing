# -*- coding: utf-8 -*-
"""ZhiYin Ops Dashboard - local operations web console (127.0.0.1:8290)."""
import json
import os
import socket
import subprocess
import time
import zipfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

# 部署约定：本目录（yumingbushu，含 ops_dashboard）是内容系统 duihuamoxing 的子目录：
#   duihuamoxing\              被监控的内容系统（Open WebUI / Ollama / 数字人 / TTS）
#   duihuamoxing\yumingbushu\  本目录（登录网关 login_gateway / 运维面板 ops_dashboard）
# 以下路径全部相对推导，不依赖固定盘符，复制到任何目录均可运行。
BASE = Path(__file__).resolve().parent        # ...\ops_dashboard
REPO_DIR = BASE.parent                        # 本目录根（yumingbushu）
ROOT = REPO_DIR.parent                        # duihuamoxing 项目根（本目录的父目录）
LOG_DIR = ROOT / 'log'
DIAG_DIR = REPO_DIR                           # diag_*.zip 诊断包生成在本仓库根目录
APP_NAME = '知音 · 运维工作台'

app = FastAPI(title=APP_NAME, docs_url=None, redoc_url=None, openapi_url=None)

LOG_FILES = [
    'webui.log', 'webui.err.log',
    'ollama.log', 'ollama.err.log',
    'tts.log', 'tts.err.log',
    'avatar.log', 'avatar.err.log',
]


def port_up(port: int) -> bool:
    s = socket.socket()
    s.settimeout(0.3)
    try:
        s.connect(('127.0.0.1', port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def _run(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return ''


def tail_file(path: Path, lines: int) -> str:
    """Read last N lines efficiently from possibly large file."""
    try:
        with open(path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            block = min(size, 65536)
            f.seek(max(0, size - block))
            data = f.read().decode('utf-8', errors='replace')
        parts = data.splitlines()
        return '\n'.join(parts[-lines:]) if lines > 0 else data
    except Exception:
        return ''


def get_gpu():
    gpu = {'available': False, 'name': '-', 'total': 0, 'used': 0, 'free': 0}
    out = _run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free',
                '--format=csv,noheader,nounits'])
    parts = [p.strip() for p in out.split(',')]
    if len(parts) == 4:
        try:
            gpu = {'available': True, 'name': parts[0], 'total': int(parts[1]),
                   'used': int(parts[2]), 'free': int(parts[3])}
        except ValueError:
            pass
    return gpu


def get_disks():
    disks = []
    out = _run(['powershell', '-NoProfile', '-Command',
                "Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -ne $null } | ForEach-Object { $_.Name + '|' + [math]::Round($_.Free/1GB,1) + '|' + [math]::Round(($_.Used+$_.Free)/1GB,1) }"])
    for line in out.splitlines():
        if '|' in line:
            n, f, t = line.split('|')[:3]
            disks.append({'drive': n + ':', 'free_gb': float(f), 'total_gb': float(t),
                          'used_gb': round(float(t) - float(f), 1)})
    return disks


@app.get('/', response_class=HTMLResponse)
def index():
    html = Path(__file__).parent / 'index.html'
    return HTMLResponse(html.read_text(encoding='utf-8'))


@app.get('/api/status')
def api_status():
    ports = {}
    for p in (8088, 8089, 11434, 48620, 8061):
        ports[str(p)] = port_up(p)

    svc = _run(['sc', 'query', 'cloudflared'])
    tunnel_up = 'RUNNING' in svc

    procs = []
    out = _run(['powershell', '-NoProfile', '-Command',
                "Get-Process | Where-Object { $_.ProcessName -match 'ollama|open-webui|python|cloudflared' } | ForEach-Object { $_.ProcessName + '|' + $_.Id + '|' + [math]::Round($_.WorkingSet64/1MB) }"])
    for line in out.splitlines():
        if '|' in line:
            n, i, m = line.split('|')[:3]
            procs.append({'name': n, 'pid': i, 'mem_mb': m})

    diag_zips = sorted([f.name for f in DIAG_DIR.glob('diag_*.zip')], reverse=True)[:5]

    return {
        'time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'ports': ports,
        'tunnel_up': tunnel_up,
        'gpu': get_gpu(),
        'disks': get_disks(),
        'procs': procs,
        'diag_zips': diag_zips,
    }


@app.get('/api/logs')
def api_logs():
    items = []
    for name in LOG_FILES:
        p = LOG_DIR / name
        if p.exists():
            items.append({'name': name, 'size': p.stat().st_size,
                          'mtime': time.strftime('%m-%d %H:%M:%S', time.localtime(p.stat().st_mtime))})
    return {'logs': items}


@app.get('/api/logs/{name}')
def api_log(name: str, lines: int = 300):
    if name not in LOG_FILES:
        raise HTTPException(404, 'unknown log')
    p = LOG_DIR / name
    if not p.exists():
        raise HTTPException(404, 'log not found')
    return {'name': name, 'content': tail_file(p, max(1, min(lines, 2000)))}


@app.get('/api/diag')
def api_diag():
    """Trigger one-click diagnostics, build zip, return name."""
    stamp = time.strftime('%Y%m%d_%H%M%S')
    zip_path = DIAG_DIR / f'diag_{stamp}.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name in LOG_FILES:
            p = LOG_DIR / name
            if p.exists():
                zf.writestr(f'logs/{name}', tail_file(p, 500))
        info = []
        info.append(f'==== ZhiYin Diagnostics {stamp} ====')
        info.append(f'Host: {os.environ.get("COMPUTERNAME", "-")}')
        info.append(f'Time: {time.strftime("%Y-%m-%d %H:%M:%S")}')
        info.append('')
        info.append('--- Ports ---')
        for p in (8088, 8089, 11434, 48620, 8061):
            info.append(f'port {p}: {"UP" if port_up(p) else "DOWN"}')
        info.append('')
        info.append('--- Tunnel ---')
        svc = _run(['sc', 'query', 'cloudflared'])
        info.append(f'cloudflared service: {"RUNNING" if "RUNNING" in svc else "STOPPED"}')
        info.append('')
        info.append('--- GPU ---')
        info.append(json.dumps(get_gpu(), ensure_ascii=False))
        info.append('')
        info.append('--- Disk ---')
        for d in get_disks():
            info.append(f"{d['drive']} free={d['free_gb']}GB total={d['total_gb']}GB")
        info.append('')
        info.append('--- Processes ---')
        out = _run(['powershell', '-NoProfile', '-Command',
                    "Get-Process | Where-Object { $_.ProcessName -match 'ollama|open-webui|python|cloudflared' } | ForEach-Object { $_.ProcessName + ' pid=' + $_.Id + ' mem=' + [math]::Round($_.WorkingSet64/1MB) + 'MB' }"])
        info.extend(out.splitlines())
        zf.writestr('system_info.txt', '\n'.join(info))
    return {'zip': zip_path.name, 'path': str(zip_path)}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8290)
