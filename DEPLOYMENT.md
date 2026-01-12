# 🚀 Production Deployment Guide

## Pre-Deployment Checklist

### ✅ Security
- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Enable authentication: `ENABLE_AUTH=true`
- [ ] Generate strong API key: `API_KEY=<random-secure-key>`
- [ ] Configure `ALLOWED_ORIGINS` with your domain(s)
- [ ] Review and restrict CORS settings
- [ ] Ensure logs directory has proper permissions
- [ ] Set up firewall rules (block direct port 3000 access if using reverse proxy)

### ✅ Configuration
- [ ] Copy `.env.example` to `.env` and customize
- [ ] Set appropriate `MAX_CONCURRENT_DOWNLOADS` based on server capacity
- [ ] Configure `JOB_TIMEOUT_HOURS` for your use case
- [ ] Review `MAX_USERNAME_LENGTH` and `MAX_URL_LENGTH` limits
- [ ] Verify download directory permissions: `chmod 755 downloads/`

### ✅ Dependencies
- [ ] Python 3.12+ installed
- [ ] All requirements installed: `pip install -r backend/requirements.txt`
- [ ] curl-cffi dependencies (optional, for better TikTok compatibility)
- [ ] SQLite3 installed
- [ ] Sufficient disk space for downloads and database

### ✅ Database
- [ ] Database file created: `tiktok_downloader.db`
- [ ] Database permissions correct: `chmod 644 tiktok_downloader.db`
- [ ] Regular backup strategy in place
- [ ] Test database migrations work

### ✅ Monitoring
- [ ] Log rotation configured (default: 10MB, 5 backups)
- [ ] Disk space monitoring for downloads directory
- [ ] Database size monitoring
- [ ] Set up alerts for service downtime

---

## Deployment Options

### Option 1: Direct Deployment (Development/Testing)

```bash
# 1. Clone repository
git clone https://github.com/Joombah/Tiktok-Bulk-Downloader.git
cd Tiktok-Bulk-Downloader

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env  # Edit configuration

# 5. Start services
chmod +x start.sh
./start.sh
```

### Option 2: Production with Systemd

#### Create Backend Service

Create `/etc/systemd/system/tiktok-downloader.service`:

```ini
[Unit]
Description=TikTok Bulk Downloader Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/tiktok-bulk-downloader
Environment="PATH=/opt/tiktok-bulk-downloader/venv/bin"
ExecStart=/opt/tiktok-bulk-downloader/venv/bin/python backend/api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tiktok-downloader
sudo systemctl start tiktok-downloader
sudo systemctl status tiktok-downloader
```

### Option 3: Production with Nginx Reverse Proxy

#### Nginx Configuration

Create `/etc/nginx/sites-available/tiktok-downloader`:

```nginx
upstream tiktok_backend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Frontend
    location / {
        root /opt/tiktok-bulk-downloader/frontend;
        try_files $uri $uri/ /index.html;
    }

    # API Backend
    location /api {
        proxy_pass http://tiktok_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Downloads (optional, for direct access)
    location /downloads {
        alias /opt/tiktok-bulk-downloader/downloads;
        autoindex on;
        auth_basic "Restricted";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/tiktok-downloader /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Option 4: Docker Deployment

#### Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p downloads logs

# Expose port
EXPOSE 3000

# Run application
CMD ["python", "backend/api.py"]
```

#### Create docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "3000:3000"
    volumes:
      - ./downloads:/app/downloads
      - ./logs:/app/logs
      - ./tiktok_downloader.db:/app/tiktok_downloader.db
    environment:
      - ENVIRONMENT=production
      - API_HOST=0.0.0.0
      - API_PORT=3000
    restart: unless-stopped

  frontend:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./frontend:/usr/share/nginx/html:ro
    restart: unless-stopped
```

Build and run:

```bash
docker-compose up -d
docker-compose logs -f
```

---

## Post-Deployment

### Verify Installation

```bash
# Check backend health
curl http://localhost:3000/api/health

# Check logs
tail -f logs/tiktok_downloader.log

# Check database
sqlite3 tiktok_downloader.db "SELECT COUNT(*) FROM profiles;"
```

### Monitoring

```bash
# Monitor disk usage
df -h downloads/

# Monitor database size
du -h tiktok_downloader.db

# Monitor logs
du -h logs/

# Check service status
systemctl status tiktok-downloader
```

### Backup Strategy

```bash
# Create backup script: /usr/local/bin/backup-tiktok.sh
#!/bin/bash
BACKUP_DIR="/backups/tiktok-downloader"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup database
sqlite3 /opt/tiktok-bulk-downloader/tiktok_downloader.db ".backup '$BACKUP_DIR/db_$DATE.sqlite'"

# Backup configuration
cp /opt/tiktok-bulk-downloader/.env "$BACKUP_DIR/env_$DATE"

# Remove old backups (keep last 7 days)
find "$BACKUP_DIR" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * /usr/local/bin/backup-tiktok.sh >> /var/log/tiktok-backup.log 2>&1
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
journalctl -u tiktok-downloader -f

# Check Python errors
python backend/api.py

# Check port availability
lsof -i :3000
```

### Database Errors

```bash
# Check database integrity
sqlite3 tiktok_downloader.db "PRAGMA integrity_check;"

# Repair database (backup first!)
sqlite3 tiktok_downloader.db ".recover" | sqlite3 new_db.db
```

### Disk Space Issues

```bash
# Find large files in downloads
find downloads/ -type f -size +100M

# Clean old downloads (be careful!)
find downloads/ -mtime +30 -type f -delete

# Vacuum database
sqlite3 tiktok_downloader.db "VACUUM;"
```

---

## Security Best Practices

1. **Never expose port 3000 directly** - Use reverse proxy
2. **Enable HTTPS** with Let's Encrypt
3. **Use strong API keys** - Generate with: `openssl rand -hex 32`
4. **Restrict CORS** - Only allow your domain
5. **Regular updates** - Keep dependencies updated
6. **Monitor logs** - Check for suspicious activity
7. **Limit file sizes** - Prevent disk filling attacks
8. **Rate limiting** - Consider adding nginx rate limits
9. **Firewall rules** - Only allow necessary ports
10. **Regular backups** - Automate database backups

---

## Performance Tuning

### For High Volume

```python
# In .env
MAX_CONCURRENT_DOWNLOADS=5
JOB_TIMEOUT_HOURS=4
```

### For Resource-Constrained Systems

```python
# In .env
MAX_CONCURRENT_DOWNLOADS=1
JOB_TIMEOUT_HOURS=1
```

### Database Optimization

```sql
-- Run periodically
VACUUM;
ANALYZE;
```

---

## Support

- 📚 Documentation: See README.md
- 🐛 Issues: https://github.com/Joombah/Tiktok-Bulk-Downloader/issues
- 💬 Discussions: https://github.com/Joombah/Tiktok-Bulk-Downloader/discussions
