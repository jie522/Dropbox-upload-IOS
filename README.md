# Dropbox 影片上傳 iPhone 捷徑

透過 iOS 捷徑（Shortcuts）手動一鍵將 iPhone 影片上傳至 Dropbox，使用 Dropbox API v2。

## 功能

- 手動選取一或多段影片，點一下即開始上傳
- 自動以日期時間命名檔案（`2024-01-15_14-30-00.MOV`）
- 支援 < 150 MB 直接上傳，≥ 150 MB 自動切換分段上傳
- 上傳完成後顯示通知

## 快速開始

### 步驟 1：建立 Dropbox App 並取得 Token

詳見 [docs/dropbox-app-setup.md](docs/dropbox-app-setup.md)

或使用輔助腳本（需要 Python 3）：

```bash
python3 get_dropbox_token.py
```

腳本會引導你完成 OAuth 授權並輸出 access token。

### 步驟 2：在 iPhone 建立捷徑

詳見 [docs/shortcut-steps.md](docs/shortcut-steps.md)

將步驟 1 取得的 access token 填入捷徑中的 `YOUR_ACCESS_TOKEN` 位置。

## 檔案說明

```
├── README.md                  # 本文件
├── get_dropbox_token.py       # 取得 Dropbox OAuth token 的輔助腳本
└── docs/
    ├── dropbox-app-setup.md   # 建立 Dropbox App 的步驟說明
    └── shortcut-steps.md      # 在 iPhone 建立捷徑的逐步教學
```

## 限制

| 條件 | 說明 |
|------|------|
| 單檔 < 150 MB | 直接上傳，速度快 |
| 單檔 ≥ 150 MB | 分段上傳，需更長時間 |
| 最大單檔 | 350 GB（Dropbox 限制） |
| 上傳時需保持捷徑在前景 | iOS 限制，無法完全背景執行 |

> **注意**：iOS Shortcuts 在螢幕鎖定後可能中斷上傳。建議上傳大型影片時保持螢幕開啟。
