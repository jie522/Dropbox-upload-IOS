#!/usr/bin/env python3
"""
Dropbox OAuth 2.0 Token 取得工具

使用方式：
    python3 get_dropbox_token.py

此腳本會：
1. 引導你到 Dropbox 授權頁面
2. 在本機啟動臨時 HTTP 伺服器接收 OAuth callback
3. 輸出 access token 供你複製到 iOS 捷徑中
"""

import hashlib
import http.server
import json
import os
import base64
import secrets
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser

AUTH_URL = "https://www.dropbox.com/oauth2/authorize"
TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"
REDIRECT_URI = "http://localhost:8765/callback"

received_code = None
received_error = None


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global received_code, received_error
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            received_code = params["code"][0]
            message = "授權成功！請回到終端機查看 access token。"
        elif "error" in params:
            received_error = params.get("error_description", ["未知錯誤"])[0]
            message = f"授權失敗：{received_error}"
        else:
            message = "未收到授權碼。"

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Dropbox 授權</title></head>
<body style="font-family:sans-serif;text-align:center;padding:40px">
<h2>{message}</h2>
<p>你可以關閉此頁面。</p>
</body></html>"""
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        pass  # 靜音 HTTP log


def generate_pkce():
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


def exchange_code_for_token(code, code_verifier, app_key):
    data = urllib.parse.urlencode({
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
        "client_id": app_key,
    }).encode()

    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    print("=" * 60)
    print("  Dropbox OAuth Token 取得工具")
    print("=" * 60)
    print()
    print("請先到 https://www.dropbox.com/developers/apps 建立 App")
    print("（詳見 docs/dropbox-app-setup.md）")
    print()

    app_key = input("請輸入你的 Dropbox App Key：").strip()
    if not app_key:
        print("錯誤：App Key 不可為空。")
        sys.exit(1)

    code_verifier, code_challenge = generate_pkce()

    params = urllib.parse.urlencode({
        "client_id": app_key,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "token_access_type": "offline",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })
    auth_url = f"{AUTH_URL}?{params}"

    # 啟動臨時 HTTP 伺服器
    server = http.server.HTTPServer(("localhost", 8765), CallbackHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.daemon = True
    thread.start()

    print()
    print("正在開啟瀏覽器進行授權...")
    print(f"若瀏覽器未自動開啟，請手動前往：\n{auth_url}")
    print()
    webbrowser.open(auth_url)

    print("等待授權完成（請在瀏覽器中點選「允許」）...")
    thread.join(timeout=120)
    server.server_close()

    if received_error:
        print(f"\n授權失敗：{received_error}")
        sys.exit(1)

    if not received_code:
        print("\n逾時或未收到授權碼，請重試。")
        sys.exit(1)

    print("正在取得 access token...")
    try:
        token_data = exchange_code_for_token(received_code, code_verifier, app_key)
    except Exception as e:
        print(f"\n取得 token 失敗：{e}")
        sys.exit(1)

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")

    print()
    print("=" * 60)
    print("  成功取得 Token！")
    print("=" * 60)
    print()
    print(f"Access Token（複製此內容到 iOS 捷徑）：")
    print(f"\n  {access_token}\n")

    if refresh_token:
        print(f"Refresh Token（選擇性儲存，用於更新 token）：")
        print(f"\n  {refresh_token}\n")

    if expires_in:
        hours = expires_in // 3600
        print(f"Access Token 有效期：約 {hours} 小時")
        print()

    print("請將 Access Token 複製到 iOS 捷徑中的「YOUR_ACCESS_TOKEN」位置。")
    print("詳見 docs/shortcut-steps.md")
    print()

    # 儲存到本機檔案（選擇性）
    save = input("是否將 token 儲存到本機 token.json？[y/N] ").strip().lower()
    if save == "y":
        with open("token.json", "w") as f:
            json.dump({
                "access_token": access_token,
                "refresh_token": refresh_token,
                "app_key": app_key,
            }, f, indent=2)
        print("已儲存至 token.json（請勿將此檔案提交到 git）")


if __name__ == "__main__":
    main()
