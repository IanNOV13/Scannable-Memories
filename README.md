# 📸 回憶足跡：雲端相簿

「回憶足跡：雲端相簿」是一個客製化的雲端相簿應用程式，於為每位使用者提供獨特的數位回憶體驗。我為每位使用者準備了一張專屬的 RFID 卡片作為禮物，使用者只需透過手機輕輕一刷，即可快速進入專屬的網站頁面。

在這裡，可以輕鬆上傳照片與影片，並根據地點快速回顧我們每天的珍貴回憶，讓美好的瞬間永存。

---

## ✨ 功能特色

- 🌻 **RFID 卡片快速登入**\
  透過客製化的 RFID 卡片，手機輕刷即可快速進入專屬相簿。

- ☁️ **共用雲端儲存**\
  每個使用者共用空間，可自由上傳照片及影片不用去找其他人傳照片或是從通訊軟體拿到壓縮的照片。

- 🗺️ **地點回顧功能**\
  方便您快速瀏覽不同地方的精彩瞬間。

- 🖥️ **直觀使用者介面**\
  採用簡潔的 HTML、CSS、JavaScript 設計。

- 🔐 **安全連線**\
  支援 Certbot SSL，確保資料傳輸的安全性。

---

## 🛠️ 技術棧

**後端**：Python 3.10.14, Flask\
**前端**：HTML, CSS, JavaScript\
**安全性**：Certbot SSL

### 📦 核心 Python 套件

- flask
- datetime
- time
- threading
- json
- dotenv
- werkzeug.utils
- os
- logging
- requests
- PIL (Pillow)
- moviepy
- io

---

## 🚀 安裝與執行

### 📌 前置條件

- Python 3.10.14 或更高版本
- Certbot (用於 SSL 憑證)

### 🔧 安裝步驟

1. 複製專案

```bash
git clone https://github.com/IanNOV13/Scannable-Memories.git
cd Scannable-Memories
```

2. 建立虛擬環境並安裝依賴

```bash
python3.10 -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

3. 設定環境變數

請在根目錄建立 `.env` 檔案，內容如下：

```env
DISCORD_WEBHOOK=你的DiscordWebhookURL
SECRET_KEY=一個階段並安全的字串
fullchain=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
privkey=/etc/letsencrypt/live/yourdomain.com/privkey.pem
```

> ⚠️ `fullchain` 和 `privkey` 請依據您的 Certbot 安裝路徑設定。

4. 啟動應用程式

```bash
python main.py
```

應用程式將會在您設定的 HTTPS 埠上運行。

---

## 🤝 貢獻指南

我們非常歡迎任何形式的貢獻！

若您有任何想法、功能建議、錯誤報告或程式碼改進，請通過 Issue 或 Pull Request 與我們聯繫。

> 💡 提交 Pull Request 前，請確保程式碼整齊、符合專案風格並通過所有測試。

---

## ⚖️ 授權協議

本專案採用「非商業使用授權」。\
您可以使用、修改和分發本專案，但**不允許用於任何商業目的**。\
使用或分發時，請加以著名原作者。

