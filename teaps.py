#!/usr/bin/env python3
"""
TEAPS v5 - Main Entry Point
Interactive setup wizard and application launcher
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_dependencies():
    """Check if all required dependencies are installed"""
    missing = []
    
    try:
        import sqlalchemy
    except ImportError:
        missing.append("sqlalchemy")
    
    try:
        import pymysql
    except ImportError:
        missing.append("pymysql")
    
    try:
        import telegram
    except ImportError:
        missing.append("python-telegram-bot")
    
    try:
        import fastapi
    except ImportError:
        missing.append("fastapi")
    
    try:
        import uvicorn
    except ImportError:
        missing.append("uvicorn")
    
    try:
        import qrcode
        from PIL import Image
    except ImportError:
        missing.append("qrcode, pillow")
    
    if missing:
        print("❌ 缺少以下依賴:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n請執行以下命令安裝:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True


def setup_database():
    """Initialize database and create tables"""
    from utils.database import get_database_url, create_all_tables
    from sqlalchemy import create_engine
    
    print("🔧 正在初始化資料庫...")
    
    try:
        db_url = get_database_url()
        engine = create_engine(db_url)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("✅ 資料庫連接成功")
        
        # Create tables
        create_all_tables(engine)
        print("✅ 資料表建立完成")
        
        return True
    
    except Exception as e:
        print(f"❌ 資料庫初始化失敗：{e}")
        return False


def setup_wizard():
    """Interactive setup wizard"""
    print("=" * 60)
    print("🚀 TEAPS v5 - Attendance & Payroll System")
    print("Setup Wizard")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Configure database
    print("\n💾 Database Configuration:")
    db_host = input("Database host (localhost): ").strip() or "localhost"
    db_port = input("Database port (3306): ").strip() or "3306"
    db_name = input("Database name (teaps_v5): ").strip() or "teaps_v5"
    db_user = input("Database user (root): ").strip() or "root"
    db_password = input("Database password: ").strip()
    
    # Save to .env file
    env_path = PROJECT_ROOT / ".env"
    
    env_content = f"""# TEAPS v5 Configuration
# Database Settings
TEAPS_DB_HOST={db_host}
TEAPS_DB_PORT={db_port}
TEAPS_DB_NAME={db_name}
TEAPS_DB_USER={db_user}
TEAPS_DB_PASSWORD={db_password}

# Telegram Bot Token (get from @BotFather)
TEAPS_TELEGRAM_BOT_TOKEN=your_bot_token_here

# QR Code Authentication Secret
QR_SECRET_KEY=your_secret_key_here

# Web Server Settings
TEAPS_WEB_HOST=0.0.0.0
TEAPS_WEB_PORT=8000
"""
    
    env_path.write_text(env_content)
    print(f"\n✅ 配置已保存至 {env_path}")
    
    # Test database connection
    if setup_database():
        print("\n🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Edit .env file and add your Telegram bot token")
        print("2. Run: python teaps.py start")
        return True
    else:
        print("\n⚠️  Database setup failed. Please check your credentials.")
        return False


def start_bot():
    """Start the Telegram bot"""
    from bot import get_bot
    
    print("🤖 Starting TEAPS Telegram Bot (Text-based, No QR Code)...")
    
    bot = get_bot()
    if not bot:
        print("❌ Failed to initialize bot. Please check your token in .env file.")
        return False
    
    # Setup database session function
    from utils.database import get_session
    bot.set_dependencies(get_session)
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")


def start_web():
    """Start the FastAPI web server"""
    import uvicorn
    from main import app
    
    host = os.getenv('TEAPS_WEB_HOST', '0.0.0.0')
    port = int(os.getenv('TEAPS_WEB_PORT', 8000))
    
    print(f"🌐 Starting TEAPS Web Server at http://{host}:{port}")
    print("📚 API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(app, host=host, port=port)


def start_all():
    """Start both bot and web server (in separate threads)"""
    import threading
    
    print("🚀 Starting TEAPS v5 System...")
    
    # Start web server in background thread
    web_thread = threading.Thread(target=start_web, daemon=True)
    web_thread.start()
    
    # Run bot in main thread
    start_bot()


def show_status():
    """Show current system status"""
    print("=" * 60)
    print("📊 TEAPS v5 System Status")
    print("=" * 60)
    
    # Check dependencies
    deps_ok = check_dependencies()
    print(f"\nDependencies: {'✅ OK' if deps_ok else '❌ Missing'}")
    
    # Check database connection
    try:
        from utils.database import get_database_url, create_all_tables
        from sqlalchemy import create_engine
        
        db_url = get_database_url()
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Database Connection: ✅ OK")
    except Exception as e:
        print(f"Database Connection: ❌ {e}")
    
    # Check bot token
    bot_token = os.getenv('TEAPS_TELEGRAM_BOT_TOKEN')
    if bot_token and len(bot_token) > 10:
        print("Telegram Bot Token: ✅ Configured")
    else:
        print("Telegram Bot Token: ❌ Not configured")
    
    # Check environment variables
    print("\nEnvironment Variables:")
    env_vars = [
        'TEAPS_DB_HOST',
        'TEAPS_DB_NAME', 
        'TEAPS_TELEGRAM_BOT_TOKEN',
        'QR_SECRET_KEY'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'TOKEN' in var or 'SECRET' in var or 'PASSWORD' in var:
                masked = value[:4] + '*' * (len(value) - 8) + value[-4:]
                print(f"  {var}: ✅ {masked}")
            else:
                print(f"  {var}: ✅ {value}")
        else:
            print(f"  {var}: ❌ Not set")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python teaps.py [command]")
        print("\nCommands:")
        print("  setup     - Run interactive setup wizard")
        print("  start     - Start Telegram bot only")
        print("  web       - Start web server only")
        print("  all       - Start both bot and web server")
        print("  status    - Show system status")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "setup":
        setup_wizard()
    elif command == "start" or command == "bot":
        start_bot()
    elif command == "web":
        start_web()
    elif command == "all":
        start_all()
    elif command == "status":
        show_status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
