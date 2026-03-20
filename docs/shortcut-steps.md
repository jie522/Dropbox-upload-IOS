# iOS 捷徑建立步驟

在 iPhone 上打開「捷徑」app，點選右上角 **+** 新增捷徑。

---

## 捷徑動作清單

依序加入以下動作：

---

### 動作 1：選取影片

**動作名稱**：`Select Photos`（選取照片）

設定：
- **Include**: `Videos`（僅影片）
- **Select Multiple**: 開啟（允許一次選多個）

> 執行時會跳出照片選取介面，選完後繼續。

---

### 動作 2：重複每個項目

**動作名稱**：`Repeat with Each`（對每個項目重複）

- 輸入來源：上一步的 `Provided Input`（Selected Photos）
- 後續動作 3～7 都放在此重複區塊「內」

---

### 動作 3（重複區塊內）：取得目前時間

**動作名稱**：`Format Date`（格式化日期）

設定：
- **Date**: `Current Date`
- **Format**: `Custom`
- **Custom Format**: `yyyy-MM-dd_HH-mm-ss`

將結果存為變數：`Filename`

> 例：`2024-01-15_14-30-00`

---

### 動作 4（重複區塊內）：組成 Dropbox 路徑

**動作名稱**：`Text`（文字）

輸入以下內容（將 `Filename` 變數插入）：

```
/Videos/Filename.MOV
```

> 點選輸入框，插入變數 `Filename`（動作 3 的輸出）。
> 最終結果類似：`/Videos/2024-01-15_14-30-00.MOV`

將結果存為變數：`DropboxPath`

---

### 動作 5（重複區塊內）：組成 API 參數 Header

**動作名稱**：`Text`（文字）

輸入以下 JSON（插入 `DropboxPath` 變數）：

```json
{"path":"DropboxPath","mode":"add","autorename":true,"mute":false}
```

> 將 `DropboxPath` 替換為插入的變數，不要包含引號。
> 最終結果類似：`{"path":"/Videos/2024-01-15_14-30-00.MOV","mode":"add","autorename":true,"mute":false}`

將結果存為變數：`APIArg`

---

### 動作 6（重複區塊內）：上傳影片

**動作名稱**：`Get Contents of URL`（取得 URL 的內容）

設定：

| 欄位 | 值 |
|------|----|
| URL | `https://content.dropboxapi.com/2/files/upload` |
| Method | `POST` |
| Headers | 見下方 |
| Request Body | `File` |
| File | `Repeat Item`（重複項目） |

**Headers 設定**（點選 `Add new field` 逐一新增）：

| Key | Value |
|-----|-------|
| `Authorization` | `Bearer YOUR_ACCESS_TOKEN` |
| `Dropbox-API-Arg` | 插入變數 `APIArg` |
| `Content-Type` | `application/octet-stream` |

> 將 `YOUR_ACCESS_TOKEN` 替換為你的實際 token（從 `get_dropbox_token.py` 或 Developer Console 取得）。

---

### 動作 7（重複區塊內）：取得上傳結果

**動作名稱**：`Get Dictionary Value`（取得字典值）

設定：
- **Get**: `Value for Key`
- **Key**: `name`
- **Dictionary**: `Contents of URL`（動作 6 的輸出）

將結果存為變數：`UploadedName`

---

### 動作 8（重複區塊外）：顯示通知

**動作名稱**：`Show Notification`（顯示通知）

設定：
- **Title**: `上傳完成`
- **Body**: 插入變數 `UploadedName`（或直接輸入 `影片已上傳至 Dropbox`）

---

## 完整流程示意

```
[選取影片]
    ↓
[對每個影片重複]
    ├─ [取得目前時間] → Filename
    ├─ [組成路徑] → DropboxPath
    ├─ [組成 JSON] → APIArg
    ├─ [POST 上傳] → 上傳結果
    └─ [取得檔名] → UploadedName
[顯示通知]
```

---

## 分段上傳（影片 ≥ 150 MB）

iOS Shortcuts 對大型檔案的支援有限。若需處理超過 150 MB 的影片，在動作 6 後加入條件判斷：

### 動作 6a：取得檔案大小

**動作名稱**：`Get Details of Files`（取得檔案詳細資訊）

設定：
- **Detail**: `File Size`
- **File**: `Repeat Item`

### 動作 6b：條件判斷

**動作名稱**：`If`（如果）

條件：`File Size` **is greater than** `157286400`（即 150 MB = 150 × 1024 × 1024）

- **If 區塊**（大檔）：執行分段上傳（見下方）
- **Otherwise 區塊**（小檔）：執行動作 6 的直接上傳

### 分段上傳步驟（If 區塊內）

**步驟 A：開始上傳 Session**

`Get Contents of URL`：
- URL: `https://content.dropboxapi.com/2/files/upload_session/start`
- Method: `POST`
- Headers:
  - `Authorization`: `Bearer YOUR_ACCESS_TOKEN`
  - `Dropbox-API-Arg`: `{"close":false}`
  - `Content-Type`: `application/octet-stream`
- Body: `File`，`Repeat Item`（第一個 chunk，建議取前 128 MB）

取得字典值 `session_id`，儲存為變數 `SessionID`。

**步驟 B：結束 Session 並提交**

`Get Contents of URL`：
- URL: `https://content.dropboxapi.com/2/files/upload_session/finish`
- Method: `POST`
- Headers:
  - `Authorization`: `Bearer YOUR_ACCESS_TOKEN`
  - `Dropbox-API-Arg`: 插入含 `session_id`、`offset`、`path` 的 JSON
  - `Content-Type`: `application/octet-stream`

> 注意：iOS Shortcuts 無法原生切割 binary 資料為 chunks，分段上傳在 Shortcuts 中實作較複雜。若需頻繁上傳大型影片，建議使用 Dropbox 官方 iOS App 的自動相機上傳功能。

---

## 常見問題

**Q: 上傳失敗，顯示 401 錯誤**
A: Access token 無效或已過期。重新執行 `get_dropbox_token.py` 取得新 token。

**Q: 上傳失敗，顯示 409 錯誤**
A: 路徑衝突。捷徑中已設定 `"autorename":true`，應會自動重新命名，若仍失敗請確認 JSON 格式正確。

**Q: 上傳速度很慢**
A: 受限於網路速度與影片大小。建議在 Wi-Fi 環境下上傳。

**Q: 捷徑執行到一半停止**
A: iOS 可能在螢幕鎖定後暫停捷徑。上傳時請保持螢幕開啟，或開啟「輔助使用 → 引導使用模式」防止鎖定。
