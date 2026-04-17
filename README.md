# TEAPS v5 - Attendance & Payroll System

雙語 Telegram 基於的出勤與薪資管理系統。

## 🚀 功能特性

### 核心功能
- ✅ **文字對話簽到系統** - 純 Telegram Bot 互動，無需掃描
- ✅ **上級確認機制** - 所有簽到記錄需管理員核准後生效
- ✅ **雙語支援** - Traditional Chinese / English
- ✅ **雙語支援** - Traditional Chinese / English
- ✅ **資料庫安全** - 敏感資料自動過濾，指數退避重試機制
- ✅ **薪資計算** - 自動計算加班費、扣款、獎金
- ✅ **Telegram Bot** - 完整的命令系統與 FSM 狀態機
- ✅ **Web Dashboard** (待完成) - Vue.js + FastAPI RESTful API

### 安全特性
- 🔒 QR Code HMAC 簽名驗證
- 🔒 One-time use 防止重放攻擊  
- 🔒 bcrypt 密碼加密
- 🔒 敏感資料日誌過濾
- 🔒 資料庫連接池與重試機制

## 💬 互動流程說明

### 員工操作流程
1. **開啟 Telegram Bot** → 發送 `/checkin`
2. **確認簽到按鈕** → 點擊 "✅ 確認簽到"
3. **等待核准** → 狀態顯示為 "⏳ 待上級核准"
4. **查詢狀態** → 使用 `/status` 查看最新狀態

### 管理員操作流程
1. **查看所有待核准記錄** → 發送 `/approve_list`
2. **點擊按鈕操作** → "✅ 核准" 或 "❌ 拒絕"
3. **員工收到通知** → 自動更新狀態並顯示結果

### 簽退流程
- 必須先有「已核准」的簽到記錄才能簽退
- `/checkout` → 確認 → 等待管理員核准


## 📋 安裝指南

### 1. 依賴安裝
```bash
cd ~/.hermes/teaps/v5
pip install -r requirements.txt
```

### 2. 環境配置
編輯 `.env` 檔案：
```env
# Database Settings
TEAPS_DB_HOST=localhost
TEAPS_DB_PORT=3306
TEAPS_DB_NAME=teaps_v5
TEAPS_DB_USER=root
TEAPS_DB_PASSWORD=your_password

# Telegram Bot Token (from @BotFather)
TEAPS_TELEGRAM_BOT_TOKEN=your_bot_token_here

# QR Code Secret Key
QR_SECRET_KEY=random_secret_key
```

### 3. 資料庫初始化
```bash
python teaps.py setup
```

## 🎯 使用方式

### Telegram Bot 命令

#### 員工命令
- `/start` - 開始使用系統
- `/checkin` - 掃描 QR Code 簽到
- `/checkout` - 掃描 QR Code 簽退
- `/status` - 查詢今日出勤狀態
- `/history [日期]` - 查詢歷史記錄
- `/payroll` - 查詢薪資資訊

#### 管理員命令
- `/approve <record_id>` - 核准出勤記錄
- `/reject <record_id>` - 拒絕出勤記錄
- `/export [月份]` - 匯出報表

### Web API 端點

```bash
# Start web server
python teaps.py web

# Access API documentation
http://localhost:8000/docs
```

主要端點：
- `POST /api/auth/login` - 使用者登入
- `GET /api/attendance/my-status` - 查詢今日出勤狀態
- `POST /api/attendance/checkin` - QR Code 簽到
- `GET /api/payroll/my-payroll` - 查詢薪資
- `POST /api/admin/approve-attendance` - 核准記錄

## 🏗️ 系統架構

```
teaps/v5/
├── models/          # SQLAlchemy ORM Models
│   ├── user.py      # User & Department models
│   ├── attendance.py # AttendanceRecord model
│   └── payroll.py   # PayrollRecord model
├── handlers/        # Business logic handlers
│   └── bot_handlers.py  # Telegram bot FSM handlers
├── utils/           # Utility modules
│   ├── database.py      # DB connection & retry mechanisms
│   ├── qrcode_auth.py   # QR code generation & validation
│   └── translations.py  # Bilingual text management
├── routes/          # API route handlers (RESTful)
├── main.py          # FastAPI application entry point
├── bot.py           # Telegram Bot implementation
└── teaps.py         # CLI entry point & setup wizard
```

## 🔧 開發指南

### 新增功能流程
1. 在 `models/` 新增 SQLAlchemy model
2. 在 `handlers/` 新增業務邏輯處理
3. 在 `routes/` 或 `main.py` 新增 API 端點
4. 在 `bot.py` 新增 Telegram 命令
5. 新增測試案例

### 測試套件
```bash
pytest tests/ -v
```

## 📊 資料庫設計

### Users Table
- employee_id (unique)
- name_tc, name_en
- email, phone
- password_hash (bcrypt)
- role (employee/manager/admin/super_admin)

### AttendanceRecords Table
- user_id (FK)
- date, check_in_time, check_out_time
- status (pending/approved/rejected)
- actual_hours, late_minutes
- qr_code_hash (audit trail)

### PayrollRecords Table
- user_id (FK)
- period_start, period_end
- base_salary, overtime_pay, bonus
- deductions (absent, late, tax)
- gross_pay, net_pay

## 🌐 雙語支援系統

使用 `BilingualText` 類別管理所有 UI 文字：
```python
from utils.translations import t, TranslationManager

# Get translation
message = t("attendance.check_in", lang="zh-TW")

# Add new translation
TranslationManager.add_translation(
    "my.new.key",
    tc="中文文字",
    en="English text"
)
```

## 🚨 安全注意事項

1. **QR Code 安全性**
   - 每 30 秒過期
   - HMAC SHA-256 簽名驗證
   - One-time use 防止重放

2. **資料庫安全**
   - 敏感字段自動過濾 (password, token, salary)
   - 連接池配置
   - 指數退避重試 (3 次：1s, 2s, 4s)

3. **密碼管理**
   - bcrypt 加密（自動 salt）
   - 最小長度檢查（建議 8+ 字符）

## 📝 待完成項目

- [ ] Vue.js Web Dashboard 前端開發
- [ ] WebSocket 實時通知系統
- [ ] Excel/PDF 報表匯出功能
- [ ] 地理位置驗證（可選配）
- [ ] Redis 会话管理（生產環境）
- [ ] JWT OAuth2 認證系統
- [ ] Docker Compose 部署配置

## 🤝 貢獻指南

1. Fork 倉庫
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

---

**版本**: 5.0.0  
**開發中**: TEAPS Team  
**最後更新**: 2026-04-17
