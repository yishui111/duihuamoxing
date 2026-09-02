# -*- coding: utf-8 -*-
"""把 loader.js 内联进原生 Open WebUI 前端 index.html（loader.js 集成入口）。

背景：Open WebUI 0.11 屏蔽 /static/*.js，静态挂载 loader.js 不生效，
因此把 loader.js 内容直接内联到 <venv>/Lib/site-packages/open_webui/frontend/index.html
的 </body> 前（带标记块，重复执行会先清除旧块，幂等）。

用法:
  python scripts/inline_loader.py           # 仓库根目录 venv 下的 open_webui
  python scripts/inline_loader.py --venv <venv路径>   # 指定其他虚拟环境
需在 Open WebUI 停止时执行，改完重启 open-webui 生效；用户浏览器 Ctrl+Shift+R 强刷。
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

parser = argparse.ArgumentParser()
parser.add_argument("--venv", default=os.path.join(ROOT, "venv"), help="open-webui 所在虚拟环境目录")
parser.add_argument("--loader", default=os.path.join(ROOT, "loader.js"), help="loader.js 路径")
args = parser.parse_args()

# 定位 open_webui 包
candidates = [
    os.path.join(args.venv, "Lib", "site-packages", "open_webui"),
    os.path.join(args.venv, "lib", "python3.12", "site-packages", "open_webui"),
    os.path.join(args.venv, "lib", "python3.11", "site-packages", "open_webui"),
    os.path.join(args.venv, "lib", "python3.10", "site-packages", "open_webui"),
]
sp = next((c for c in candidates if os.path.isdir(c)), None)
if not sp:
    print("ERROR: 在 %s 下未找到 open_webui 包，请确认 venv 已安装 open-webui" % args.venv)
    sys.exit(1)

# 定位 index.html（新版在 frontend/，兼容 static/）
idx = None
for cand in [os.path.join(sp, "frontend", "index.html"),
             os.path.join(sp, "build", "index.html"),
             os.path.join(sp, "static", "index.html")]:
    if os.path.isfile(cand):
        idx = cand
        break
if not idx:
    for root, _dirs, files in os.walk(sp):
        if "index.html" in files:
            idx = os.path.join(root, "index.html")
            break
if not idx:
    print("ERROR: 找不到 open_webui 的 index.html")
    sys.exit(1)
print("index.html:", idx)

loader = args.loader
if not os.path.isfile(loader):
    print("ERROR: loader.js 不存在:", loader)
    sys.exit(1)

html = open(idx, encoding="utf-8").read()
js = open(loader, encoding="utf-8").read()

# 1. 移除 <script src="/static/loader.js"...></script>
html = re.sub(r'<script[^>]*src=["\']/static/loader\.js["\'][^>]*></script>', "", html)

# 2. 移除旧的内联块（防重复）
MARK = "<!-- dsh-loader-inline:start -->"
END = "<!-- dsh-loader-inline:end -->"
if MARK in html:
    html = re.sub(re.escape(MARK) + r".*?" + re.escape(END), "", html, flags=re.S)

# 3. 内联到 </body> 前（body 已就绪，loader.js 可直接 appendChild）
if "</body>" not in html:
    print("ERROR: 找不到 </body>"); sys.exit(1)
inline = MARK + "\n<script>\n" + js + "\n</script>\n" + END
html = html.replace("</body>", inline + "\n</body>", 1)

open(idx, "w", encoding="utf-8").write(html)
print("内联完成, index.html 大小:", os.path.getsize(idx))
