# TEAPS v5 - Unraid Docker 部署完整指南

## 🎯 前言

本指南將指導您在 **Unraid NAS** 上透過 Docker 部署 **TEAPS v5 Attendance & Payroll System**。

### 系統需求
- Unraid OS 6.12+ (推薦最新版本)
- Docker 插件已啟用
- GitHub 倉庫訪問權限
- Telegram Bot Token (@BotFather)

---

## 📋 方法一：使用 Community Applications (手動配置 - 推薦新手)

### Step 1: 安裝 Community Applications
1. 開啟 Unraid Web UI
2. 進入 **Plugins** → **Install Plugin**
3. 輸入 URL: `https://raw.githubusercontent.com/Squidwards/communityapplications/master/plugins/community.applications.plugin`
4. 點擊 **Install**

### Step 2: 安裝 Docker Manager
1. 在 Community Applications 中搜尋 "Docker Manager"
2. 點擊 **Install**
3. 等待安裝完成並重啟 Unraid (如需)

### Step 3: 手動配置 TEAPS v5 容器

#### 3.1 進入 Docker Manager
- 前往 **Apps** → **Docker**
- 點擊 **Add Container** (+)
- 選擇 **Advanced View** (高級視圖)

#### 3.2 基本設置
```yaml
Name: teaps-v5
Repository: johnnyhsu56788/teaps-v5
Tag: latest
# 如果無法拉取，可先下載到本地並上傳
```

#### 3.3 Port Mappings (端口映射)
| Host Port | Container Port | Protocol | Description |
|-----------|---------------|----------|-------------|
| 8000 | 8000 | TCP | Web API & Dashboard |
| 8765 | 8765 | UDP | Optional for debugging |

#### 3.4 Volume Mappings (磁碟映射)
| Host Path | Container Path | Description |
|-----------|---------------|-------------|
| `/mnt/user/appdata/teaps-v5/config` | `/app/config` | 配置文件存儲 |
| `/mnt/user/appdata/teaps-v5/logs` | `/app/logs` | 日誌文件存儲 |
| `/mnt/user/appdata/teaps-v5/.env` | `/app/.env` | 環境變數 (只讀) |

#### 3.5 Environment Variables (環境變數)
點擊 **Add Path** → **Environment Variable**:

```bash
TEAPS_DB_HOST=192.168.x.x          # 您的 MySQL 容器 IP 或外部資料庫 IP
TEAPS_DB_PORT=3306
TEAPS_DB_NAME=teaps_v5
TEAPS_DB_USER=teaps_user
TEAPS_DB_PASSWORD=your_secure_password_here
TEAPS_TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
QR_SECRET_KEY=auto_generated
TEAPS_WEB_HOST=0.0.0.0
TEAPS_WEB_PORT=8000
```

**重要提示**: 
- 如果沒有外部 MySQL，請先安裝 MySQL Docker 容器 (見下方)
- Telegram Bot Token 請從 @BotFather 獲取

#### 3.6 Auto Restart & Resources
- **Restart Policy**: Always
- **CPU Limit**: 2.0 cores
- **Memory Limit**: 1GB RAM

#### 3.7 創建容器
點擊 **Apply** → 等待容器啟動成功。

---

## 📋 方法二：使用 Compose App (進階用戶)

### Step 1: 安裝 Compose App 插件
1. 進入 **Community Applications**
2. 搜尋 "Compose App"
3. 點擊 **Install**
4. 重啟 Unraid

### Step 2: 下載 Docker Compose 文件
```bash
# 在您的電腦上執行
cd ~/Downloads
git clone https://github.com/johnnyhsu56788/teaps-v5.git
cd teaps-v5
cp .env.example .env
nano .env  # 編輯環境變數
```

### Step 3: 上傳到 Unraid
1. 將 `.env` 文件複製到 Unraid 的共享目錄 (如 `/mnt/user/appdata/teaps-v5/`)
2. 在 Compose App 中點擊 **Add Template**
3. 選擇 `docker-compose.yml` 文件路徑

### Step 4: 配置與啟動
1. 編輯環境變數 (自動從 `.env` 讀取)
2. 確認端口和卷映射正確
3. 點擊 **Create** → **Start**

---

## 🗄️ 方法三：同時部署 MySQL 容器

如果您沒有外部 MySQL，建議在 Unraid 上安裝 MySQL:

### Step 1: 添加 MySQL 容器
- **Name**: teaps-mysql
- **Repository**: `mysql:8.0`
- **Tag**: latest

#### Port Mappings
| Host Port | Container Port | Protocol |
|-----------|---------------|----------|
| 3306 | 3306 | TCP |

#### Volume Mappings
| Host Path | Container Path | Description |
|-----------|---------------|-------------|
| `/mnt/user/appdata/mysql` | `/var/lib/mysql` | MySQL 數據持久化 |

#### Environment Variables
```bash
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_DATABASE=teaps_v5
MYSQL_USER=teaps_user
MYSQL_PASSWORD=your_user_password
```

### Step 2: 配置初始化腳本
1. 創建文件 `/mnt/user/appdata/mysql/init-db.sql`
2. 複製 `scripts/init-db.sql` 內容到此文件
3. MySQL 容器啟動時會自動執行

---

## 📝 步驟 4: 驗證部署

### 1. 檢查容器狀態
```bash
# 在 Unraid Web UI → Docker → Containers
Status: Running (綠色)
Health: Healthy
```

### 2. 訪問 Web API
- **URL**: `http://your-unraid-ip:8000`
- **API Docs**: `http://your-unraid-ip:8000/docs`
- **Health Check**: `http://your-unraid-ip:8000/health`

### 3. 測試 Telegram Bot
```bash
# 在 Telegram 中搜尋您的 Bot
/start → 查看歡迎訊息
/checkin → 測試簽到功能
/status → 查詢狀態
```

---

## 🔧 故障排除

### 問題 1: 容器無法啟動
**解決方案**:
```bash
# 檢查日誌
Docker Manager → teaps-v5 → Logs

# 常見原因:
- .env 文件配置錯誤
- MySQL 連接失敗
- 端口衝突 (檢查其他服務是否使用 8000)
```

### 問題 2: Telegram Bot 無回應
**解決方案**:
1. 確認 `.env` 中的 `TEAPS_TELEGRAM_BOT_TOKEN` 正確
2. 檢查 Unraid 防火牆是否允許出站連接
3. 查看日誌: `docker logs teaps-v5 | grep -i telegram`

### 問題 3: MySQL 連接失敗
**解決方案**:
1. 確認 MySQL 容器已啟動並健康
2. 檢查 `.env` 中的 DB_HOST 是否正確 (使用容器名稱或 IP)
3. 測試連接: `docker exec teaps-v5 mysql -h teaps-mysql -u teaps_user -p`

---

## 🔄 更新與維護

### 更新容器版本
```bash
# 在 Docker Manager 中:
1. 停止容器
2. 刪除容器 (保留數據卷)
3. 拉取最新鏡像
4. 重新創建容器 (使用相同配置)
5. 啟動容器
```

### 備份數據
```bash
# MySQL 資料庫備份
docker exec teaps-mysql mysqldump -u teaps_user -p teaps_v5 > /mnt/user/backups/teaps_backup.sql

# 配置文件備份
cp /mnt/user/appdata/teaps-v5/.env /mnt/user/backups/.env.backup
```

### 恢復數據
```bash
# 恢復資料庫
cat backup.sql | docker exec -i teaps-mysql mysql -u teaps_user -p teaps_v5
```

---

## 🎯 Unraid 特定優化建議

### 1. 使用 SSD Cache (如果可用)
- 將 MySQL 數據卷 (`/mnt/user/appdata/mysql`) 設置在 SSD cache pool
- 提升資料庫性能

### 2. 配置 Portainer (可選)
```bash
# 安裝 Portainer 容器進行更強大的管理
docker run -d -p 8000:9443 --name portainer --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  portainer/portainer-ce
```

### 3. 設置自動更新
- 使用 **Watchtower** 容器自動更新 Docker 鏡像
- 配置 Unraid 的 **Scheduled Tasks** 定期備份

---

## 📚 參考資源

- **Unraid Docker 文檔**: https://unraid.net/docs/docker
- **TEAPS v5 API 文檔**: http://your-unraid-ip:8000/docs
- **GitHub 倉庫**: https://github.com/johnnyhsu56788/teaps-v5

---

## ✅ 完成清單

- [ ] 安裝 Community Applications 插件
- [ ] 安裝 Docker Manager
- [ ] 配置 MySQL 容器 (可選)
- [ ] 配置 TEAPS v5 容器
- [ ] 設置環境變數
- [ ] 啟動並驗證服務
- [ ] 測試 Telegram Bot
- [ ] 設置自動備份

---

**🎉 恭喜！您已成功在 Unraid 上部署 TEAPS v5!**

如有任何問題，請查看日誌或參考上述故障排除部分。
