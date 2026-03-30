# 🌤 WeatherBot Taiwan

Line Bot：根據 GPS 位置自動推播台灣天氣變化與縣市切換通知

---

## 功能

- 📍 傳送位置 → 即時查詢當地天氣
- ⚠️ 天氣有重大變化時自動推播通知
- 🗺 移動到不同縣市時自動推播新縣市天氣
- 🔄 每 30 分鐘背景檢查天氣

## 技術架構

- **後端**：Python + Flask
- **Bot**：Line Messaging API
- **天氣資料**：中央氣象署開放資料平台（免費）
- **地理編碼**：Nominatim（OpenStreetMap，免費）
- **資料庫**：SQLite
- **排程**：APScheduler
- **部署**：Render（免費方案）

---

## 本地開發環境設定

### 1. 安裝套件

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

```bash
cp .env.example .env
# 編輯 .env 填入你的 API keys
```

### 3. 申請必要 API

**Line Bot（免費）**
1. 前往 https://developers.line.biz
2. 建立新的 Provider
3. 建立 Messaging API Channel
4. 取得 Channel Access Token 與 Channel Secret

**中央氣象署 API（免費）**
1. 前往 https://opendata.cwa.gov.tw
2. 註冊帳號
3. 申請 API 授權碼

### 4. 啟動本地伺服器

```bash
python run.py
# 或:
uvicorn weatherbot.app:app --reload --port 5000
```

### 5. 使用 ngrok 讓 Line 能連到你的本地伺服器

```bash
# 安裝 ngrok 後執行
ngrok http 5000
```

把 ngrok 給的 HTTPS URL 填入 Line Bot 的 Webhook URL：
```
https://你的ngrok網址/callback
```

---

## 部署到 Render（免費）

1. 推上 GitHub
2. 到 https://render.com 建立新的 Web Service
3. 連結你的 GitHub repo
4. 設定環境變數（LINE_CHANNEL_ACCESS_TOKEN、LINE_CHANNEL_SECRET、CWA_API_KEY）
5. Start Command 設為：`gunicorn app:app`
6. 把 Render 給的網址填入 Line Bot Webhook URL

---

## 專案結構

```
weatherbot/
├── app.py          # Flask 主程式，Line Webhook 處理
├── weather.py      # 天氣 API 串接、縣市解析、變化偵測
├── database.py     # SQLite 資料庫操作
├── scheduler.py    # 排程推播邏輯
├── requirements.txt
├── .env.example
└── README.md
```
