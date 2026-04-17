# TEAPS v5 - MySQL for Unraid Docker Configuration
# 專為 Unraid 優化的 MySQL 容器配置

## 🐳 MySQL 容器設置

### Basic Settings
- **Name**: teaps-mysql
- **Repository**: mysql:8.0
- **Tag**: latest

### Port Mappings
| Host Port | Container Port | Protocol | Description |
|-----------|---------------|----------|-------------|
| 3306 | 3306 | TCP | MySQL Database |

### Volume Mappings
| Host Path | Container Path | Description |
|-----------|---------------|-------------|
| `/mnt/user/appdata/mysql` | `/var/lib/mysql` | MySQL 數據持久化 (重要!) |
| `/mnt/user/appdata/mysql/init-db.sql` | `/docker-entrypoint-initdb.d/init-db.sql` | 初始化腳本 |

### Environment Variables
```bash
MYSQL_ROOT_PASSWORD=your_root_password_here
MYSQL_DATABASE=teaps_v5
MYSQL_USER=teaps_user
MYSQL_PASSWORD=your_user_password_here
```

### Auto Restart
- **Policy**: Always

---

## 📝 步驟 1: 創建數據目錄

在 Unraid 的文件瀏覽器中創建以下目錄結構：
```
/mnt/user/appdata/
└── mysql/
    ├── data (自動創建)
    └── init-db.sql (手動創建，見下方)
```

---

## 📝 步驟 2: 創建初始化腳本

在 `/mnt/user/appdata/mysql/init-db.sql` 中貼上以下內容：

```sql
USE teaps_v5;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(20) UNIQUE NOT NULL,
    name_tc VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('employee', 'manager', 'admin', 'super_admin') DEFAULT 'employee',
    department_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- Create departments table
CREATE TABLE IF NOT EXISTS departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name_tc VARCHAR(200) NOT NULL,
    name_en VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    manager_id INT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES users(id)
);

-- Create attendance_records table
CREATE TABLE IF NOT EXISTS attendance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    date DATE NOT NULL,
    check_in_time TIMESTAMP NULL,
    check_out_time TIMESTAMP NULL,
    break_duration_minutes INT DEFAULT 0,
    check_in_location VARCHAR(255),
    check_out_location VARCHAR(255),
    scheduled_hours DECIMAL(3,1) DEFAULT 8.0,
    actual_hours DECIMAL(4,2) DEFAULT 0.0,
    status ENUM('pending', 'approved', 'rejected', 'late', 'early_leave', 'absent') DEFAULT 'pending',
    late_minutes INT DEFAULT 0,
    early_leave_minutes INT DEFAULT 0,
    manager_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_date (user_id, date),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create payroll_records table
CREATE TABLE IF NOT EXISTS payroll_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    base_salary DECIMAL(10,2) NOT NULL,
    attendance_days INT DEFAULT 0,
    scheduled_days INT DEFAULT 0,
    overtime_hours DECIMAL(5,2) DEFAULT 0.0,
    overtime_rate DECIMAL(3,2) DEFAULT 1.5,
    overtime_pay DECIMAL(10,2) DEFAULT 0.0,
    bonus DECIMAL(10,2) DEFAULT 0.0,
    allowance DECIMAL(10,2) DEFAULT 0.0,
    deduction_absent DECIMAL(10,2) DEFAULT 0.0,
    deduction_late DECIMAL(10,2) DEFAULT 0.0,
    deduction_other DECIMAL(10,2) DEFAULT 0.0,
    tax_deduction DECIMAL(10,2) DEFAULT 0.0,
    social_security DECIMAL(10,2) DEFAULT 0.0,
    gross_pay DECIMAL(10,2) DEFAULT 0.0,
    net_pay DECIMAL(10,2) DEFAULT 0.0,
    status ENUM('pending', 'approved', 'paid', 'rejected', 'hold') DEFAULT 'pending',
    approved_by INT,
    approved_at TIMESTAMP NULL,
    paid_at TIMESTAMP NULL,
    notes TEXT,
    manager_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_period (user_id, period_start),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

-- Create demo admin user
INSERT INTO users (employee_id, name_tc, name_en, email, password_hash, role) 
VALUES ('ADMIN001', '系統管理員', 'System Administrator', 'admin@teaps.local', 
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILp92S.0i', 
        'super_admin')
ON DUPLICATE KEY UPDATE name_tc = VALUES(name_tc);

-- Create demo department
INSERT INTO departments (code, name_tc, name_en) 
VALUES ('HR001', '人力資源部', 'Human Resources Department')
ON DUPLICATE KEY UPDATE name_tc = VALUES(name_tc);
```

---

## 🔄 更新 MySQL 密碼

如果您需要修改 MySQL 密碼：

1. **停止 MySQL 容器**
2. **編輯 `.env` 文件或 Unraid 配置**
3. **刪除數據卷** (警告: 會清除所有數據!)
4. **重新創建容器**

---

## 📊 監控與維護

### 查看 MySQL 日誌
```bash
# 在 Unraid Docker Manager → teaps-mysql → Logs
```

### 訪問 MySQL 命令行
```bash
# 在 Unraid Terminal 執行:
docker exec -it teaps-mysql mysql -u teaps_user -p
# 輸入密碼
USE teaps_v5;
SHOW TABLES;
SELECT * FROM users LIMIT 5;
```

### 備份 MySQL 數據
```bash
# 在 Unraid Terminal:
docker exec teaps-mysql mysqldump -u teaps_user -p teaps_v5 > /mnt/user/backups/mysql_backup.sql
```

---

## ⚠️ 重要注意事項

1. **不要刪除 `/mnt/user/appdata/mysql`** - 這會清除所有資料庫數據!
2. **定期備份** - 使用 Unraid 的 Scheduled Tasks 自動備份
3. **密碼管理** - 將 MySQL 密碼保存在安全的地方
4. **版本升級** - 升級 MySQL 版本前請先備份數據

---

## ✅ 完成檢查清單

- [ ] 創建 `/mnt/user/appdata/mysql` 目錄
- [ ] 上傳 `init-db.sql` 初始化腳本
- [ ] 配置 Docker 容器
- [ ] 設置環境變數
- [ ] 啟動容器並確認健康狀態
- [ ] 測試資料庫連接
- [ ] 創建 MySQL 數據備份方案

---

**🎉 MySQL for Unraid 已準備就緒!**

接下來請繼續部署 TEAPS v5 應用容器。
