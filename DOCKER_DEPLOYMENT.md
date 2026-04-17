# TEAPS v5 - Docker Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Docker Engine >= 20.10
- Docker Compose >= 2.0
- MySQL client (optional, for manual database access)

### Step 1: Configure Environment Variables

Create a `.env` file in the same directory as `docker-compose.yml`:

```bash
cp .env.example .env
nano .env  # Edit with your settings
```

Required variables:
```env
# Database Configuration
TEAPS_DB_PASSWORD=your_secure_root_password
TEAPS_DB_USER_PASSWORD=your_user_password

# Telegram Bot (get from @BotFather)
TEAPS_TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Optional: QR Code Secret (auto-generated if not set)
QR_SECRET_KEY=your_custom_secret_key_if_desired
```

### Step 2: Start Services

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f teaps

# Check status
docker-compose ps
```

### Step 3: Access the Application

- **Web API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Telegram Bot**: Automatically running in background

---

## 📊 Service Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Nginx     │────▶│    TEAPS     │────▶│    MySQL    │
│  (Port 80)  │     │  App (8000)  │     │  (3306)     │
│  (HTTPS)    │     │              │     │             │
└─────────────┘     └──────────────┘     └─────────────┘
```

---

## 🔧 Common Operations

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f teaps
docker-compose logs -f mysql
```

### Access Database Shell
```bash
docker exec -it teaps_mysql mysql -u teaps_user -pteaps_user_password teaps_v5
```

### Execute Database Migrations (if needed)
```bash
docker-compose exec teaps python teaps.py setup
```

### Backup Database
```bash
docker exec teaps_mysql mysqldump -u teaps_user -pteaps_user_password teaps_v5 > backup.sql
```

### Restore Database
```bash
cat backup.sql | docker exec -i teaps_mysql mysql -u teaps_user -pteaps_user_password teaps_v5
```

---

## 🌐 Production Deployment with Nginx

### 1. Update Nginx Configuration

Edit `nginx.conf` and change:
```nginx
server_name your-domain.com;  # Replace with your actual domain
```

### 2. Generate SSL Certificates (using Let's Encrypt)

```bash
# Install certbot
docker run -v /path/to/ssl:/etc/nginx/ssl certbot/certbot certonly \
  --webroot -w /var/www/html -d your-domain.com

# Or use docker-compose with certbot service
```

### 3. Update .env for Production

```env
TEAPS_WEB_HOST="0.0.0.0"
TEAPS_TELEGRAM_BOT_TOKEN=your_production_bot_token
```

### 4. Deploy with Nginx

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔒 Security Best Practices

### 1. Use Strong Passwords
```env
TEAPS_DB_PASSWORD=$(openssl rand -base64 32)
TEAPS_DB_USER_PASSWORD=$(openssl rand -base64 32)
```

### 2. Rotate Secrets Regularly
Update `.env` file and restart:
```bash
docker-compose down
# Edit .env
docker-compose up -d
```

### 3. Limit Database Exposure
- MySQL port (3306) only accessible internally
- Use Docker network isolation
- Never expose MySQL to public internet

### 4. Enable HTTPS in Production
Use Let's Encrypt or your preferred CA for SSL certificates

---

## 🛠️ Troubleshooting

### Application Won't Start
```bash
# Check logs
docker-compose logs teaps

# Common issues:
# - Database not ready (wait for mysql health check)
# - Missing .env file
# - Port conflicts (change ports in docker-compose.yml)
```

### Database Connection Failed
```bash
# Test connectivity
docker exec -it teaps_mysql mysqladmin ping -h localhost

# Check database exists
docker exec -it teaps_mysql mysql -u root -p -e "SHOW DATABASES;"
```

### Telegram Bot Not Responding
```bash
# Verify token in .env
grep TEAPS_TELEGRAM_BOT_TOKEN .env

# Check bot logs
docker-compose logs teaps | grep -i telegram
```

---

## 📈 Monitoring & Maintenance

### Health Checks
All services include health checks. View status:
```bash
docker inspect --format='{{.State.Health.Status}}' teaps_mysql
docker inspect --format='{{.State.Health.Status}}' teaps_app
```

### Resource Usage
```bash
docker stats
```

### Cleanup Old Images
```bash
docker image prune -a
```

---

## 🔄 Updates & Upgrades

### Pull Latest Code
```bash
git pull origin main
```

### Rebuild Containers
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Schema Updates
If you add new models, run migrations:
```bash
docker-compose exec teaps python teaps.py setup
```

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [MySQL Docker Hub](https://hub.docker.com/_/mysql)

---

## 🆘 Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review this guide
3. Check GitHub Issues for similar problems
4. Contact TEAPS v5 development team

---

**Version**: 5.0.0  
**Last Updated**: 2026-04-17
