#!/bin/bash
# TEAPS v5 - Unraid Quick Setup Script
# 這個腳本用於在您的電腦上生成配置，然後上傳到 Unraid

set -e

echo "=================================================="
echo "🚀 TEAPS v5 - Unraid 快速部署準備"
echo "=================================================="

PROJECT_DIR="~/Downloads/teaps-v5-unraid-setup"
mkdir -p "$PROJECT_DIR"

# Step 1: Clone GitHub repository
echo -e "\n📥 Step 1: 克隆 GitHub 倉庫..."
cd ~
git clone https://github.com/johnnyhsu56788/teaps-v5.git teaps-v5-source
cp -r teaps-v5-source/* "$PROJECT_DIR/"

# Step 2: Create .env template for Unraid
echo -e "\n📝 Step 2: 創建環境變數模板..."
cat > "$PROJECT_DIR/.env.unraid" << 'EOF'
# TEAPS v5 - Unraid Environment Variables
# Replace the values below with your actual configuration

# Database Configuration (MySQL)
TEAPS_DB_HOST=192.168.1.XX        # Change to your MySQL container IP or hostname
TEAPS_DB_PORT=3306
TEAPS_DB_NAME=teaps_v5
TEAPS_DB_USER=teaps_user
TEAPS_DB_PASSWORD=your_secure_password_here

# Telegram Bot Token (Get from @BotFather)
TEAPS_TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Optional QR Code Secret (auto-generated if not set)
QR_SECRET_KEY=optional_secret_key

# Web Server Configuration
TEAPS_WEB_HOST=0.0.0.0
TEAPS_WEB_PORT=8000
EOF

echo "✅ 環境變數模板已創建：$PROJECT_DIR/.env.unraid"

# Step 3: Create Unraid Docker configuration file
echo -e "\n🐳 Step 3: 創建 Unraid Docker 配置文件..."
cat > "$PROJECT_DIR/unraid-docker-config.txt" << 'EOF'
==================================================
TEAPS v5 - Unraid Docker 配置指南
==================================================

1. 進入 Unraid Web UI → Apps → Docker → Add Container (Advanced View)

2. Basic Settings:
   Name: teaps-v5
   Repository: johnnyhsu56788/teaps-v5
   Tag: latest

3. Port Mappings:
   Host Port    | Container Port | Protocol
   8000         | 8000           | TCP (Web API)
   8765         | 8765           | UDP (Optional)

4. Volume Mappings:
   Host Path                        | Container Path      | Description
   /mnt/user/appdata/teaps-v5/config| /app/config         | Configuration files
   /mnt/user/appdata/teaps-v5/logs  | /app/logs           | Log files
   /mnt/user/appdata/teaps-v5/.env  | /app/.env           | Environment variables (Read-Only)

5. Environment Variables:
   TEAPS_DB_HOST=192.168.x.x        # Your MySQL container IP
   TEAPS_DB_PORT=3306
   TEAPS_DB_NAME=teaps_v5
   TEAPS_DB_USER=teaps_user
   TEAPS_DB_PASSWORD=[YOUR_PASSWORD]
   TEAPS_TELEGRAM_BOT_TOKEN=[YOUR_BOT_TOKEN]
   QR_SECRET_KEY=auto_generated
   TEAPS_WEB_HOST=0.0.0.0
   TEAPS_WEB_PORT=8000

6. Auto Restart: Always
7. CPU Limit: 2.0 cores
8. Memory Limit: 1GB RAM

9. Click "Apply" to create the container!

==================================================
EOF

# Step 4: Create README for Unraid deployment
echo -e "\n📚 Step 4: 創建部署說明文件..."
cp "$PROJECT_DIR/../unraid-deployment-guide.md" "$PROJECT_DIR/README-Unraid-Setup.md"

# Step 5: Summary
echo ""
echo "=================================================="
echo "✅ Unraid 部署準備完成!"
echo "=================================================="
echo ""
echo "📁 已創建的檔案:"
echo "   $PROJECT_DIR/.env.unraid              (環境變數模板)"
echo "   $PROJECT_DIR/unraid-docker-config.txt (Docker 配置指南)"
echo "   $PROJECT_DIR/README-Unraid-Setup.md   (完整部署說明)"
echo ""
echo "🚀 下一步操作:"
echo "   1. 將上述文件上傳到 Unraid (/mnt/user/appdata/teaps-v5/)"
echo "   2. 根據 unraid-docker-config.txt 配置 Docker 容器"
echo "   3. 編輯 .env.unraid 填入您的實際配置"
echo "   4. 啟動容器並訪問 http://your-unraid-ip:8000"
echo ""
echo "🔗 GitHub 倉庫：https://github.com/johnnyhsu56788/teaps-v5"
echo "=================================================="

# Show the files created
ls -la "$PROJECT_DIR/"
