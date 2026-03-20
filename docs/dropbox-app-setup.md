# 建立 Dropbox App 並取得 Access Token

## 方法一：使用輔助腳本（推薦）

完成下方步驟 1-4 後，執行：

```bash
python3 get_dropbox_token.py
```

腳本會自動完成 OAuth 流程並輸出 access token。

---

## 方法二：手動取得 Token（最簡單，僅限個人帳號）

### 步驟 1：前往 Dropbox Developer Console

開啟 https://www.dropbox.com/developers/apps

### 步驟 2：建立新 App

1. 點選 **Create app**
2. 選擇 API：**Scoped access**
3. 選擇存取範圍：**App folder**（只允許存取專屬資料夾，較安全）
   - 或選 **Full Dropbox**（可存取整個 Dropbox）
4. 輸入 App 名稱，例如 `iphone-video-upload`
5. 點選 **Create app**

### 步驟 3：設定權限

在 App 設定頁面，切換到 **Permissions** 分頁，勾選：

- `files.content.write`（上傳檔案）
- `files.metadata.write`（寫入中繼資料）

點選 **Submit** 儲存。

### 步驟 4：取得 App Key

在 **Settings** 分頁，記下：
- **App key**（後續腳本會用到）
- **App secret**（請妥善保管）

### 步驟 5：產生 Access Token（手動方式）

在 **Settings** 分頁，找到 **OAuth 2** 區塊：

1. 點選 **Generate** 按鈕（Generate access token）
2. 複製產生的 token

> **注意**：此方式產生的 token 為長效 token，請妥善保管，勿分享給他人。

---

## 將 Token 加入 iOS 捷徑

取得 token 後，繼續參考 [shortcut-steps.md](shortcut-steps.md) 建立捷徑。

在捷徑中找到 `YOUR_ACCESS_TOKEN` 並替換為你的 token。

---

## 安全提醒

- Access token 等同帳號密碼，請勿公開分享
- 不要將 token 提交到 git（`token.json` 已在 `.gitignore` 中排除）
- 若 token 外洩，立即到 Developer Console 重新產生
