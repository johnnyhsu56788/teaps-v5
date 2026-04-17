# 🎯 TEAPS v5 - Unraid Docker 完整部署指南

## 📋 目錄

1. [前置準備](#前置準備)
2. [方法一：手動配置 (推薦新手)](#方法一手動配置-推薦新手)
3. [方法二：Compose App (進階用戶)](#方法二compose-app-進階用戶)
4. [MySQL 容器部署](#mysql-容器部署)
5. [驗證與測試](#驗證與測試)
6. [故障排除](#故障排除)
7. [維護與備份](#維護與備份)

---

## 🚀 前置準備

### 系統需求
- ✅ Unraid OS 6.12+ (推薦最新版本)
- ✅ Docker 插件已啟用
- ✅ GitHub 倉庫訪問權限: `https://github.com/johnnyhsu56788/teaps-v5`
- ✅ Telegram Bot Token (從 @BotFather 獲取)

### 下載文件清單
請確保以下文件存在於您的 Unraid 系統中：
```
/mnt/user/appdata/teaps-v5/
├── .env                          # 環境變數配置
├── docker-compose.yml            # Docker Compose (可選)
└── scripts/
    └── init-db.sql               # MySQL 初始化腳本
```

---

## 📦 方法一：手動配置 (推薦新手)

### Step 1: 安裝必要插件
1. **Community Applications**
   - URL: `https://raw.githubusercontent.com/Squidwards/communityapplications/master/plugins/community.applications.plugin`
   - 位置：Unraid → Plugins → Install Plugin

2. **Docker Manager** (如果未預裝)
   - 在 Community Applications 中搜尋並安裝 "Docker"

### Step 2: 添加 MySQL 容器 (可選但推薦)

#### 基本設置
- **Name**: `teaps-mysql`
- **Repository**: `mysql:8.0`
- **Tag**: `latest`

#### Port Mappings
| Host | Container | Protocol |
|------|-----------|----------|
| 3306 | 3306 | TCP |

#### Volume Mappings
| Host Path | Container Path | Description |
|-----------|---------------|-------------|
| `/mnt/user/appdata/mysql` | `/var/lib/mysql` | MySQL 數據持久化 |
| `/mnt/user/appdata/mysql/init-db.sql` | `/docker-entrypoint-initdb.d/init-db.sql` | 初始化腳本 |

#### Environment Variables
```bash
MYSQL_ROOT_PASSWORD=your_secure_password
MYSQL_DATABASE=teaps_v5
MYSQL_USER=teaps_user
MYSQL_PASSWORD=your_user_password
```

### Step 3: 添加 TEAPS v5 容器

#### 基本設置
- **Name**: `teaps-v5`
- **Repository**: `johnnyhsu56788/teaps-v5`
- **Tag**: `latest`

#### Port Mappings
| Host | Container | Protocol | Description |
|------|-----------|----------|-------------|
| 8000 | 8000 | TCP | Web API & Dashboard |
| 8765 | 8765 | UDP | Optional debugging |

#### Volume Mappings
| Host Path | Container Path | Description |
|-----------|---------------|-------------|
| `/mnt/user/appdata/teaps-v5/config` | `/app/config` | 配置文件 |
| `/mnt/user/appdata/teaps-v5/logs` | `/app/logs` | 日誌文件 |
| `/mnt/user/appdata/teaps-v5/.env` | `/app/.env` | 環境變數 (只讀) |

#### Environment Variables
```bash
TEAPS_DB_HOST=192.168.x.x        # MySQL 容器 IP 或主機名
TEAPS_DB_PORT=3306
TEAPS_DB_NAME=teaps_v5
TEAPS_DB_USER=teaps_user
TEAPS_DB_PASSWORD=your_user_password
TEAPS_TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
QR_SECRET_KEY=auto_generated
TEAPS_WEB_HOST=0.0.0.0
TEAPS_WEB_PORT=8000
```

#### Advanced Settings
- **Auto Restart**: Always
- **CPU Limit**: 2.0 cores
- **Memory Limit**: 1GB RAM

### Step 4: 創建 .env 文件

在 Unraid 的文件瀏覽器中創建 `/mnt/user/appdata/teaps-v5/.env`:

```bash
TEAPS_DB_HOST=teaps-mysql
TEAPS_DB_PORT=3306
TEAPS_DB_NAME=teaps_v5
TEAPS_DB_USER=teaps_user
TEAPS_DB_PASSWORD=your_secure_password
TEAPS_TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
QR_SECRET_KEY=auto_generated
TEAPS_WEB_HOST=0.0.0.0
TEAPS_WEB_PORT=8000
```

### Step 5: 啟動容器

1. 點擊 **Apply** 創建容器
2. 等待狀態顯示為 **Running** (綠色)
3. 檢查 **Health** 狀態

---

## 📦 方法二：Compose App (進階用戶)

### Step 1: 安裝 Compose App 插件
- Community Applications → 搜尋 "Compose App" → Install

### Step 2: 上傳 docker-compose.yml
```bash
# 在您的電腦上
cd ~/Downloads
git clone https://github.com/johnnyhsu56788/teaps-v5.git
cp teaps-v5/.env.example teaps-v5/.env
nano teaps-v5/.env  # 編輯配置

# 上傳到 Unraid
scp -r teaps-v5 user@your-unraid-ip:/mnt/user/appdata/
```

### Step 3: 使用 Compose App 部署
1. 進入 **Apps → Docker → Compose**
2. 點擊 **Add Template**
3. 選擇 `/mnt/user/appdata/teaps-v5/docker-compose.yml`
4. 確認環境變數自動讀取
5. 點擊 **Create** → **Start**

---

## 🗄️ MySQL 容器部署詳情

### 初始化腳本位置
確保以下文件存在：
```
/mnt/user/appdata/mysql/init-db.sql
```

內容來自: `scripts/init-db.sql` (已在 GitHub 倉庫中)

### 驗證 MySQL 運行
```bash
# 在 Unraid Terminal:
docker exec -it teaps-mysql mysql -u teaps_user -p
# 輸入密碼後執行:
USE teaps_v5;
SHOW TABLES;
```

---

## ✅ 驗證與測試

### 1. Web API 訪問
- **URL**: `http://your-unraid-ip:8000`
- **API Docs**: `http://your-unraid-ip:8000/docs`
- **Health Check**: `http://your-unraid-ip:8000/health`

### 2. Telegram Bot 測試
在 Telegram 中：
1. 搜尋您的 Bot
2. 發送 `/start` → 查看歡迎訊息
3. 發送 `/checkin` → 確認按鈕出現
4. 點擊確認 → 檢查狀態

### 3. 資料庫驗證
```bash
docker exec -it teaps-mysql mysql -u teaps_user -pteaps_v5 -e "SELECT * FROM users LIMIT 1;"
```

---

## 🔧 故障排除

### 問題 1: 容器無法啟動
**檢查**:
- `.env` 文件路徑是否正確
- MySQL 是否已啟動且健康
- 端口是否有衝突 (8000, 3306)
- 日誌: `Docker Manager → teaps-v5 → Logs`

### 問題 2: Telegram Bot 無回應
**檢查**:
- `TEAPS_TELEGRAM_BOT_TOKEN` 是否正確
- Unraid 是否能訪問外部網路
- 日誌: `docker logs teaps-v5 | grep -i telegram`

### 問題 3: MySQL 連接失敗
**檢查**:
- TEAPS_DB_HOST 是否正確 (使用容器名稱 `teaps-mysql`)
- MySQL 密碼是否匹配 `.env` 配置
- 防火牆設置

---

## 🔄 維護與備份

### 自動更新鏡像
```bash
# 在 Unraid Terminal:
docker pull johnnyhsu56788/teaps-v5:latest
# 重新創建容器 (保留數據卷)
```

### 資料庫備份
**手動備份**:
```bash
docker exec teaps-mysql mysqldump -u teaps_user -pteaps_v5 > /mnt/user/backups/mysql_backup_$(date +%Y%m%d).sql
```

**自動備份 (使用 Unraid Scheduled Tasks)**:
1. 進入 **Settings → Scheduled Tasks**
2. 添加新任務，每天執行一次:
   ```bash
   docker exec teaps-mysql mysqldump -u teaps_user -pteaps_v5 > /mnt/user/backups/mysql_backup_$(date +\%Y\%m\%d).sql
   ```

### 配置文件備份
```bash
cp /mnt/user/appdata/teaps-v5/.env ~/backups/.env.backup
```

---

## 📊 Unraid 特定優化

### SSD Cache
- 將 MySQL 數據卷設置在 SSD cache pool: `/mnt/user/appdata/mysql` → **Cache Pool**

### Portainer (可選)
安裝 Portainer 進行更強大的容器管理:
```bash
docker run -d -p 8000:9443 --name portainer \
  -v /var/run/docker.sock:/var/run/docker.sock \
  portainer/portainer-ce
```

### Log Rotation
在 Unraid Docker 設置中配置日誌輪轉，避免磁碟空間耗盡。

---

## 📚 參考資源

- **GitHub 倉庫**: https://github.com/johnnyhsu56788/teaps-v5
- **Unraid Docker 文檔**: https://unraid.net/docs/docker
- **TEAPS v5 API 文檔**: http://your-unraid-ip:8000/docs

---

## ✅ 完成檢查清單

- [ ] 安裝 Community Applications 插件
- [ ] 安裝 Docker Manager (如果未預裝)
- [ ] 創建數據目錄結構
- [ ] 部署 MySQL 容器
- [ ] 上傳初始化腳本 `init-db.sql`
- [ ] 配置 TEAPS v5 容器環境變數
- [ ] 創建 `.env` 文件
- [ ] 啟動並驗證所有服務
- [ ] 測試 Telegram Bot 功能
- [ ] 設置自動備份任務

---

## 🎉 恭喜！

您已成功在 Unraid 上部署 **TEAPS v5 Attendance & Payroll System**!

如有任何問題，請參考上述故障排除部分或訪問 GitHub 倉庫查看最新文檔。

**版本**: TEAPS v5.0  
**最後更新**: 2026-04-17  
**授權**: Proprietary (All rights reserved)
