#!/bin/bash
# TEAPS v5 - Deployment Script
# Automated deployment to production environment

set -e  # Exit on error

# Configuration
PROJECT_DIR="$HOME/.hermes/teaps/v5"
BACKUP_DIR="$HOME/.hermes/teaps/backups"
LOG_DIR="$HOME/.hermes/teaps/logs"
ENV_FILE="$PROJECT_DIR/.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Create backups
create_backup() {
    log_info "Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/teaps_v5_$TIMESTAMP.tar.gz"
    
    tar -czf "$BACKUP_FILE" -C "$PROJECT_DIR" . 2>/dev/null || {
        log_warn "Backup failed or project directory empty, continuing..."
        return 0
    }
    
    log_info "Backup created: $BACKUP_FILE"
}

# Step 2: Install dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    cd "$PROJECT_DIR"
    
    # Create virtual environment if not exists
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log_info "Dependencies installed successfully"
}

# Step 3: Database setup
setup_database() {
    log_info "Setting up database..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Check if .env exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error ".env file not found. Please run 'python teaps.py setup' first."
        exit 1
    fi
    
    # Run database initialization
    python teaps.py status || {
        log_warn "Database connection test failed. Check your .env configuration."
        return 1
    }
    
    log_info "Database setup completed"
}

# Step 4: Start services
start_services() {
    log_info "Starting TEAPS v5 services..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Create log directory
    mkdir -p "$LOG_DIR"
    
    # Start web server in background
    nohup python teaps.py web > "$LOG_DIR/web_server.log" 2>&1 &
    WEB_PID=$!
    echo $WEB_PID > "$LOG_DIR/web_server.pid"
    
    log_info "Web server started (PID: $WEB_PID)"
    
    # Start Telegram bot in background
    nohup python teaps.py start > "$LOG_DIR/telegram_bot.log" 2>&1 &
    BOT_PID=$!
    echo $BOT_PID > "$LOG_DIR/telegram_bot.pid"
    
    log_info "Telegram bot started (PID: $BOT_PID)"
    
    # Wait for services to initialize
    sleep 3
    
    log_info "All services started successfully!"
}

# Step 5: Run tests
run_tests() {
    log_info "Running test suite..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    pytest tests/ -v --tb=short || {
        log_error "Tests failed. Deployment aborted."
        exit 1
    }
    
    log_info "All tests passed!"
}

# Step 6: Health check
health_check() {
    log_info "Performing health checks..."
    
    sleep 2
    
    # Check web server
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log_info "Web server: ✅ Healthy"
    else
        log_error "Web server: ❌ Not responding"
        return 1
    fi
    
    # Check process status
    if [ -f "$LOG_DIR/web_server.pid" ]; then
        WEB_PID=$(cat "$LOG_DIR/web_server.pid")
        if kill -0 $WEB_PID 2>/dev/null; then
            log_info "Web server process: ✅ Running"
        else
            log_error "Web server process: ❌ Not running"
            return 1
        fi
    fi
    
    if [ -f "$LOG_DIR/telegram_bot.pid" ]; then
        BOT_PID=$(cat "$LOG_DIR/telegram_bot.pid")
        if kill -0 $BOT_PID 2>/dev/null; then
            log_info "Telegram bot process: ✅ Running"
        else
            log_error "Telegram bot process: ❌ Not running"
            return 1
        fi
    fi
    
    log_info "All health checks passed!"
}

# Rollback function
rollback() {
    log_warn "Rolling back to previous version..."
    
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/teaps_v5_*.tar.gz 2>/dev/null | head -2 | tail -1)
    
    if [ -n "$LATEST_BACKUP" ]; then
        tar -xzf "$LATEST_BACKUP" -C "$PROJECT_DIR"
        log_info "Rollback completed from: $LATEST_BACKUP"
    else
        log_error "No backup found for rollback!"
        exit 1
    fi
}

# Main deployment process
main() {
    echo "=========================================="
    echo "🚀 TEAPS v5 Deployment Script"
    echo "=========================================="
    
    case "$1" in
        deploy)
            create_backup
            install_dependencies
            setup_database
            run_tests || rollback
            start_services
            health_check
            ;;
        backup)
            create_backup
            ;;
        restore)
            rollback
            ;;
        status)
            cd "$PROJECT_DIR"
            source venv/bin/activate 2>/dev/null || {
                log_error "Virtual environment not found. Run 'deploy.sh deploy' first."
                exit 1
            }
            python teaps.py status
            ;;
        stop)
            log_info "Stopping services..."
            
            if [ -f "$LOG_DIR/web_server.pid" ]; then
                kill $(cat "$LOG_DIR/web_server.pid") 2>/dev/null || true
                rm "$LOG_DIR/web_server.pid"
                log_info "Web server stopped"
            fi
            
            if [ -f "$LOG_DIR/telegram_bot.pid" ]; then
                kill $(cat "$LOG_DIR/telegram_bot.pid") 2>/dev/null || true
                rm "$LOG_DIR/telegram_bot.pid"
                log_info "Telegram bot stopped"
            fi
            ;;
        logs)
            tail -f "$LOG_DIR/"*.log
            ;;
        *)
            echo "Usage: $0 {deploy|backup|restore|status|stop|logs}"
            echo ""
            echo "Commands:"
            echo "  deploy   - Full deployment (backup, install, test, start)"
            echo "  backup   - Create manual backup"
            echo "  restore  - Rollback to latest backup"
            echo "  status   - Check system status"
            echo "  stop     - Stop all services"
            echo "  logs     - View live logs"
            exit 1
            ;;
    esac
}

# Run main function with arguments
main "$@"

