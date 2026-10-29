#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
feishu_webhook_listener.py — 飛書「一鍵發布」本地監聽程式

用途：在飛書表格做一個「自動化」按鈕/勾選 → 呼叫 webhook → 本程式收到後
      執行 `python tools/sync_from_feishu.py --build --push`，把飛書改動推上線。

運作方式：
  - 監聽 http://0.0.0.0:<PORT>/webhook （PORT 預設 8899，可用環境變數 LISTEN_PORT 改）
  - 收到 POST 且 secret 正確 → 背景執行同步+上線，回傳 {"ok":true}
  - GET  /health → {"ok":true} 可用來探活

安全性：
  - secret 來自 tools/.feishu_secret.json 的 "webhook_secret" 欄，或環境變數 WEBHOOK_SECRET。
  - 未設定 secret 時本程式會隨機產生一組並印出，請把它填進飛書自動化的 webhook 網址
    查詢參數（例如 http://主機:8899/webhook?secret=xxxx）。

重要：飛書雲端要能連到本程式，本機必須「對外可達」。
  - 同一台電腦、飛書網頁在本地瀏覽器開 → 可用 http://localhost:8899（但飛書自動化是雲端發出，
    仍需要公開網址）。
  - 最簡單做法：用 cloudflared / ngrok 把本機 8899 暴露成一個公開 https 網址，
    再把該網址填進飛書自動化的 webhook。
  - 若不想暴露公開網址，直接用 sync_push.bat（雙擊）或每日排程+手動 push 即可。

啟動：
  python tools/feishu_webhook_listener.py
（建議用背景方式常駐；關掉就無法從飛書遠端觸發。）
"""

import os
import sys
import json
import subprocess
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_FILE = os.path.join(ROOT, "tools", ".feishu_secret.json")
PORT = int(os.environ.get("LISTEN_PORT", "8899"))

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
if not WEBHOOK_SECRET and os.path.exists(SECRET_FILE):
    try:
        WEBHOOK_SECRET = json.load(open(SECRET_FILE, encoding="utf-8")).get("webhook_secret", "")
    except Exception:
        pass
if not WEBHOOK_SECRET:
    import secrets
    WEBHOOK_SECRET = secrets.token_hex(16)
    print("[資訊] 未設定 webhook_secret，已隨機產生：%s" % WEBHOOK_SECRET)
    print("        請把此值設為 tools/.feishu_secret.json 的 webhook_secret，")
    print("        或做為飛書 webhook 網址的 ?secret= 參數。")


def run_sync():
    """背景執行同步+上線。"""
    try:
        subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "sync_from_feishu.py"),
             "--build", "--push"],
            cwd=ROOT, check=True)
        print("[listener] 同步+上線完成。")
    except Exception as e:
        print("[listener] 同步失敗：%s" % e)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?")[0] in ("/health", "/"):
            self._send(200, {"ok": True})
        else:
            self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        path = self.path.split("?")[0]
        if path != "/webhook":
            self._send(404, {"ok": False, "error": "not found"})
            return
        # 驗證 secret：查詢參數或 JSON body
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        secret_in = qs.get("secret", [None])[0]
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            body = {}
        if not secret_in:
            secret_in = body.get("secret")
        if secret_in != WEBHOOK_SECRET:
            self._send(403, {"ok": False, "error": "unauthorized"})
            return
        # 背景執行，立即回應
        threading.Thread(target=run_sync, daemon=True).start()
        self._send(200, {"ok": True, "message": "sync triggered"})

    def log_message(self, *args):
        pass  # 安靜


def main():
    srv = HTTPServer(("0.0.0.0", PORT), Handler)
    print("[listener] 監聽中 http://0.0.0.0:%d/webhook （Ctrl+C 停止）" % PORT)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[listener] 已停止。")


if __name__ == "__main__":
    main()
