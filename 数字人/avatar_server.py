# -*- coding: utf-8 -*-
"""
RAG 知识库 - 数字人素材服务（完整版，迁移 light-avatar 原版功能）
=================================================================
提供 light-avatar 原版全部功能（建库工具 preprocess.html + 主页面 index.html）：
  GET  /                      -> avatar_web/index.html（数字人主页面）
  GET  /web/<路径>             -> avatar_web 静态文件
  GET  /core/<路径>            -> avatar_core 模块（页面 import 用）
  GET  /api/libs               -> 素材库列表
  GET  /api/lib/<库>/<路径>     -> 素材库文件（manifest / frames/*.jpg）
  POST /api/lib/<库>/<路径>     -> 上传素材文件（body 为文件字节）
  POST /api/transcode          -> 视频转码（上传原始视频 -> H.264，body 为视频字节）
  GET  /api/input/<路径>        -> 转码后的视频（建库工具播放用）
素材库目录默认项目内 avatar_libs（LIGHT_AVATAR_LIBS 可覆盖）；
视频输入目录 avatar_input（本项目内）；监听 0.0.0.0:48620（AVATAR_PORT 可覆盖）。
纯 Python 标准库实现，不吃配置（约 20MB 内存，无 GPU）。
"""
import base64
import json
import logging
import os
import re
import shutil
import subprocess
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging.handlers import RotatingFileHandler
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.abspath(__file__))
# 素材库：项目内置 avatar_libs（完全自包含，随项目复制即用）；可用 LIGHT_AVATAR_LIBS 覆盖
LIBS = os.environ.get("LIGHT_AVATAR_LIBS", os.path.join(ROOT, "avatar_libs"))
WEB_DIR = os.path.join(ROOT, "avatar_web")
CORE_DIR = os.path.join(ROOT, "avatar_core")
INPUT_DIR = os.path.join(ROOT, "avatar_input")
PORT = int(os.environ.get("AVATAR_PORT", "48620"))
FFMPEG = os.environ.get("FFMPEG_PATH", os.path.join(ROOT, "runtime", "ffmpeg", "bin", "ffmpeg.exe"))
FFPROBE = os.environ.get("FFPROBE_PATH", os.path.join(ROOT, "runtime", "ffmpeg", "bin", "ffprobe.exe"))

# ---- 日志（写 data/logs/avatar.log，5MB 轮转，保留 3 份历史）----
_LOG_DIR = os.environ.get("AVATAR_LOG_DIR", os.path.join(os.path.dirname(ROOT), "data", "logs"))
os.makedirs(_LOG_DIR, exist_ok=True)
logger = logging.getLogger("avatar_server")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _fh = RotatingFileHandler(
        os.path.join(_LOG_DIR, "avatar.log"),
        maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8",
    )
    _fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(_fh)


def log_ui(action, detail=""):
    """前端操作日志（loader.js 通过 POST /api/log 上报），写 ui.log。"""
    try:
        _ui = logging.getLogger("avatar_ui")
        _ui.setLevel(logging.INFO)
        if not _ui.handlers:
            _fh = RotatingFileHandler(
                os.path.join(_LOG_DIR, "ui.log"),
                maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8",
            )
            _fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            _fh.setLevel(logging.INFO)
            _ui.addHandler(_fh)
        _ui.info("[%s] %s", action, detail)
    except Exception:
        pass


MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".ico": "image/x-icon",
    ".svg": "image/svg+xml",
}


def _safe(root, rel):
    """防路径穿越：返回 root 下 rel 的绝对路径；越界返回 None。"""
    base = os.path.abspath(root)
    target = os.path.abspath(os.path.join(base, rel))
    if target != base and not target.startswith(base + os.sep):
        return None
    return target


def list_libs():
    out = []
    if os.path.isdir(LIBS):
        for name in sorted(os.listdir(LIBS)):
            d = os.path.join(LIBS, name)
            if os.path.isdir(d) and os.path.isfile(os.path.join(d, "manifest.json")):
                out.append(name)
    return out


class Handler(BaseHTTPRequestHandler):
    server_version = "avatar-server"
    # HTTP/1.1 keep-alive：全部响应都带 Content-Length，浏览器可复用连接，
    # 嘴型帧等大量小图请求省去每次 TCP 握手
    protocol_version = "HTTP/1.1"

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def _send_error(self, code, msg="Not Found"):
        """带 CORS 头的错误响应（浏览器跨域时也能看到真实错误）。"""
        try:
            data = ("%d %s" % (code, msg)).encode("utf-8")
            self.send_response(code, msg)
            self._cors()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)
        except Exception:
            pass

    def _json(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _file(self, path):
        """流式发送文件：64KB 分块（大视频不吃整块内存）+ ETag 协商缓存
        （嘴型帧/manifest 反复加载时命中 304，不再每次全量重传；
        文件更新后 ETag 变化，浏览器拿到的仍是新内容）。"""
        ext = os.path.splitext(path)[1].lower()
        ct = MIME.get(ext, "application/octet-stream")
        try:
            st = os.stat(path)
        except OSError:
            self._send_error(404)
            return
        etag = '"%d-%d"' % (st.st_mtime_ns, st.st_size)
        if self.headers.get("If-None-Match", "").strip() == etag:
            self.send_response(304)
            self._cors()
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            return
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(st.st_size))
        self.send_header("ETag", etag)
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if self.command == "HEAD":
            return
        try:
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            # 客户端中途断开：连接已不可复用，必须关闭（HTTP/1.1 keep-alive 要求）
            self.close_connection = True

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = unquote(self.path)
        try:
            if path == "/api/libs":
                self._json(200, {"libs": list_libs()})
                return
            if path.startswith("/api/lib/"):
                rel = path[len("/api/lib/"):]
                target = _safe(LIBS, rel)
                if target and os.path.isfile(target):
                    self._file(target)
                    return
                self._send_error(404)
                return
            if path.startswith("/api/input/"):
                rel = path[len("/api/input/"):]
                target = _safe(INPUT_DIR, rel)
                if target and os.path.isfile(target):
                    self._file(target)
                    return
                self._send_error(404)
                return
            if path == "/" or path == "":
                self._file(os.path.join(WEB_DIR, "index.html"))
                return
            if path.startswith("/web/"):
                rel = path[len("/web/"):]
                target = _safe(WEB_DIR, rel)
                if target and os.path.isfile(target):
                    self._file(target)
                    return
                self._send_error(404)
                return
            if path.startswith("/core/"):
                rel = path[len("/core/"):]
                target = _safe(CORE_DIR, rel)
                if target and os.path.isfile(target):
                    self._file(target)
                    return
                self._send_error(404)
                return
            # 兼容：/api/upload 保留（4 图上传），可选
            if path == "/api/upload":
                self._json(200, {"libs": list_libs()})
                return
            self._send_error(404)
        except Exception:
            self._send_error(500)

    def do_POST(self):
        path = unquote(self.path)
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b""

            # 前端操作日志上报：POST /api/log，body = {"action": "...", "detail": "..."}
            if path == "/api/log":
                try:
                    raw = body.decode("utf-8", "ignore").lstrip("\ufeff \t\r\n")
                    obj = json.loads(raw) if raw else {}
                    log_ui(obj.get("action", "?"), obj.get("detail", ""))
                except Exception as e:
                    log_ui("api/log解析异常", "%r" % (e,))
                self._json(200, {"ok": True})
                return

            # 视频转码：body = 视频字节
            if path == "/api/transcode":
                if length > 500 * 1024 * 1024:
                    self._json(413, {"error": "too large"})
                    return
                # 毫秒时间戳 + 随机后缀：多线程下两路上传同毫秒也不会互相覆盖
                base = "upload_%d_%s" % (int(time.time() * 1000), uuid.uuid4().hex[:8])
                os.makedirs(INPUT_DIR, exist_ok=True)
                src = os.path.join(INPUT_DIR, base + ".mp4")
                with open(src, "wb") as f:
                    f.write(body)
                codec = ""
                if os.path.isfile(FFPROBE):
                    try:
                        r = subprocess.run(
                            [FFPROBE, "-v", "error", "-select_streams", "v:0",
                             "-show_entries", "stream=codec_name", "-of", "csv=p=0", src],
                            capture_output=True, timeout=60)
                        codec = r.stdout.decode("utf-8", "ignore").strip()
                    except Exception:
                        pass
                file = base + ".mp4"
                transcoded = False
                if codec != "h264" and os.path.isfile(FFMPEG):
                    out = os.path.join(INPUT_DIR, base + "_h264.mp4")
                    try:
                        subprocess.run(
                            [FFMPEG, "-y", "-i", src, "-c:v", "libx264", "-preset", "fast",
                             "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac",
                             "-movflags", "+faststart", out],
                            capture_output=True, timeout=300)
                        if os.path.isfile(out):
                            file = base + "_h264.mp4"
                            transcoded = True
                    except Exception:
                        pass
                self._json(200, {"file": file, "transcoded": transcoded,
                                 "codec": codec, "url": "/api/input/" + file})
                return

            # 素材上传：POST /api/lib/<库>/<相对路径>，body = 文件字节
            if path.startswith("/api/lib/"):
                rel = path[len("/api/lib/"):]
                if length > 100 * 1024 * 1024:
                    self._json(413, {"error": "too large"})
                    return
                target = _safe(LIBS, rel)
                if not target:
                    self._json(400, {"error": "路径越界"})
                    return
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "wb") as f:
                    f.write(body)
                self._json(200, {"ok": True, "path": rel, "bytes": length})
                return

            # 4 图上传（可选保留）
            if path == "/api/upload":
                obj = json.loads(body.decode("utf-8")) if body else {}
                name = (obj.get("name") or "").strip()
                images = obj.get("images") or {}
                if not re.fullmatch(r"[A-Za-z0-9_\u4e00-\u9fff]{1,30}", name):
                    self._json(400, {"error": "人物名只能含中文/字母/数字/下划线，长度 1-30"})
                    return
                lib_dir = os.path.join(LIBS, name)
                frames_dir = os.path.join(lib_dir, "frames")
                os.makedirs(frames_dir, exist_ok=True)
                frame_files = []
                for key, slot in (("m0", 0), ("m1", 1), ("m2", 2), ("m3", 3)):
                    data_url = images.get(key) or ""
                    m = re.match(r"data:image/(jpeg|png|webp|gif);base64,(.+)", data_url)
                    if not m:
                        continue
                    ext = "jpg" if m.group(1) == "jpeg" else m.group(1)
                    raw = base64.b64decode(m.group(2))
                    fname = "mouth%d.%s" % (slot, ext)
                    with open(os.path.join(frames_dir, fname), "wb") as f:
                        f.write(raw)
                    frame_files.append({"id": "M%d" % slot, "file": "frames/" + fname, "slot": slot})
                if not frame_files:
                    self._json(400, {"error": "请至少上传闭嘴图(m0)"})
                    return
                manifest = {
                    "meta": {"name": name, "person": name, "created": time.strftime("%Y-%m-%d"),
                             "note": "上传生成"},
                    "frames": sorted(frame_files, key=lambda x: x["slot"]),
                    "clips": [],
                }
                with open(os.path.join(lib_dir, "manifest.json"), "w", encoding="utf-8") as f:
                    json.dump(manifest, f, ensure_ascii=False, indent=2)
                self._json(200, {"ok": True, "lib": name, "frames": len(frame_files)})
                return

            self._send_error(404)
        except Exception:
            self._send_error(500)

    def do_DELETE(self):
        """删除素材库：DELETE /api/lib/<库名>（只删 avatar_libs 下的用户库，保护内置测试库）"""
        path = unquote(self.path)
        try:
            if not path.startswith("/api/lib/"):
                self._send_error(404)
                return
            rel = path[len("/api/lib/"):].strip("/")
            # 库名只允许字母/数字/下划线/横线，防路径穿越
            if not re.fullmatch(r"[A-Za-z0-9_\-]{1,50}", rel):
                self._json(400, {"error": "库名不合法"})
                return
            # 保护内置测试库
            if rel.startswith("lib_test"):
                self._json(403, {"error": "内置测试库不可删除"})
                return
            target = _safe(LIBS, rel)
            if not target or not os.path.isdir(target):
                self._json(404, {"error": "素材库不存在"})
                return
            shutil.rmtree(target)
            log_ui("删除素材库", "%s（删除成功，剩余库: %s）" % (rel, ",".join(list_libs())))
            self._json(200, {"ok": True, "deleted": rel})
        except Exception:
            self._send_error(500)

    def log_message(self, *args):
        # 记录所有请求：客户端 -> 方法 路径
        try:
            logger.info("%s -> %s %s", self.client_address[0], self.command, self.path)
        except Exception:
            pass


if __name__ == "__main__":
    print("avatar-server: port=%s libs=%s web=%s" % (PORT, LIBS, WEB_DIR), flush=True)
    # 多线程：转码/大文件传输不再阻塞嘴型帧等并发请求
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.daemon_threads = True
    server.serve_forever()
