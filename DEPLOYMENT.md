# DigitalOcean Droplet Deployment Guide

This guide walks through deploying The Word Registry to a DigitalOcean droplet with Nginx reverse proxy for zero-downtime deployments.

## Prerequisites

- DigitalOcean account
- Domain name pointed to your droplet's IP
- Stripe account (test or live keys)
- SSH access to your droplet

## Droplet Requirements

**Recommended Specs:**
- **Droplet Size:** Basic Droplet ($12/month or higher)
  - 2 GB RAM / 1 CPU (minimum)
  - 4 GB RAM / 2 CPUs (recommended)
- **OS:** Ubuntu 22.04 LTS
- **Region:** Choose closest to your users

## Initial Server Setup

### 1. Create and Access Droplet

```bash
# SSH into your droplet
ssh root@your_droplet_ip
```

### 2. Create Non-Root User

```bash
# Create user
adduser wordregistry
usermod -aG sudo wordregistry

# Set up SSH for new user
rsync --archive --chown=wordregistry:wordregistry ~/.ssh /home/wordregistry

# Switch to new user
su - wordregistry
```

### 3. Update System

```bash
sudo apt update
sudo apt upgrade -y
```

## Install Dependencies

### 1. Install Python 3.13

```bash
# Add deadsnakes PPA
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.13
sudo apt install python3.13 python3.13-venv python3.13-dev -y

# Verify installation
python3.13 --version
```

### 2. Install Node.js 20

```bash
# Install Node.js via NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

# Verify installation
node --version
npm --version
```

### 3. Install PostgreSQL

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify installation
sudo -u postgres psql --version
```

### 4. Install Nginx

```bash
# Install Nginx
sudo apt install nginx -y

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Verify installation
sudo systemctl status nginx
```

### 5. Install Git

```bash
sudo apt install git -y
```

## Database Setup

### 1. Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE word_registry;
CREATE USER wordregistry_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE word_registry TO wordregistry_user;
\q
```

### 2. Configure PostgreSQL for Local Access

```bash
# Edit pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Add this line (if not already present):
# local   all             all                                     md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

## Application Setup

### 1. Clone Repository

```bash
# Create app directory
sudo mkdir -p /var/www/word-registry
sudo chown wordregistry:wordregistry /var/www/word-registry

# Clone repository
cd /var/www/word-registry
git clone https://github.com/yourusername/word-registry.git .
```

### 2. Backend Setup

```bash
cd /var/www/word-registry/backend

# Create virtual environment
python3.13 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create production .env file
nano .env
```

**Backend `.env` configuration:**
```env
# Database
DATABASE_URL=postgresql://wordregistry_user:your_secure_password_here@localhost:5432/word_registry

# Stripe (use live keys for production)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Rate Limiting
RATE_LIMIT_ENABLED=True
REDIS_URL=  # Leave empty for in-memory (or add Redis later)

# Environment
ENVIRONMENT=production
```

### 3. Initialize Database

```bash
# Still in backend/ with venv activated
python init_db.py
python import_words.py
python verify_import.py
```

### 4. Test Backend

```bash
# Test that backend runs
uvicorn app.main:app --host 0.0.0.0 --port 8000

# In another terminal, test:
curl http://localhost:8000/health

# Stop test server (Ctrl+C)
```

### 5. Frontend Setup

```bash
cd /var/www/word-registry/frontend

# Install dependencies
npm install

# Create production .env.local
nano .env.local
```

**Frontend `.env.local` configuration:**
```env
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

### 6. Build Frontend

```bash
# Build for production
npm run build

# Test build
npm run start

# Stop test server (Ctrl+C)
```

## Systemd Service Setup

### 1. Create Backend Service

```bash
sudo nano /etc/systemd/system/word-registry-backend.service
```

**Service file contents:**
```ini
[Unit]
Description=Word Registry Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=wordregistry
WorkingDirectory=/var/www/word-registry/backend
Environment="PATH=/var/www/word-registry/backend/venv/bin"
ExecStart=/var/www/word-registry/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Create Frontend Service

```bash
sudo nano /etc/systemd/system/word-registry-frontend.service
```

**Service file contents:**
```ini
[Unit]
Description=Word Registry Frontend
After=network.target

[Service]
Type=simple
User=wordregistry
WorkingDirectory=/var/www/word-registry/frontend
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="NODE_ENV=production"
ExecStart=/usr/bin/npm run start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable word-registry-backend
sudo systemctl enable word-registry-frontend

# Start services
sudo systemctl start word-registry-backend
sudo systemctl start word-registry-frontend

# Check status
sudo systemctl status word-registry-backend
sudo systemctl status word-registry-frontend
```

## Nginx Configuration

### 1. Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/word-registry
```

**Nginx configuration (see `nginx.conf` file for complete config)**

### 2. Enable Site

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/word-registry /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

## SSL/HTTPS Setup with Let's Encrypt

### 1. Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 2. Obtain SSL Certificate

```bash
# Replace with your domain
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow prompts:
# - Enter email address
# - Agree to terms
# - Choose redirect HTTP to HTTPS (option 2)
```

### 3. Test Auto-Renewal

```bash
sudo certbot renew --dry-run
```

## Stripe Webhook Configuration

### 1. Configure Webhook Endpoint

1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Enter URL: `https://yourdomain.com/api/payment/webhook`
4. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
5. Copy webhook signing secret

### 2. Update Backend .env

```bash
sudo nano /var/www/word-registry/backend/.env

# Add webhook secret:
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here

# Restart backend
sudo systemctl restart word-registry-backend
```

## Deployment Updates (Zero Downtime)

### 1. Create Update Script

```bash
nano /var/www/word-registry/deploy.sh
```

**See `deploy.sh` for complete script**

### 2. Make Executable

```bash
chmod +x /var/www/word-registry/deploy.sh
```

### 3. Run Deployment

```bash
cd /var/www/word-registry
./deploy.sh
```

## Monitoring and Logs

### View Logs

```bash
# Backend logs
sudo journalctl -u word-registry-backend -f

# Frontend logs
sudo journalctl -u word-registry-frontend -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Check Service Status

```bash
sudo systemctl status word-registry-backend
sudo systemctl status word-registry-frontend
sudo systemctl status nginx
sudo systemctl status postgresql
```

## Firewall Setup

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow OpenSSH

# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'

# Check status
sudo ufw status
```

## Database Backups

### 1. Create Backup Script

```bash
sudo nano /usr/local/bin/backup-word-registry.sh
```

**Backup script:**
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/word-registry"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
sudo -u postgres pg_dump word_registry | gzip > $BACKUP_DIR/word_registry_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/word_registry_$DATE.sql.gz"
```

### 2. Make Executable and Schedule

```bash
sudo chmod +x /usr/local/bin/backup-word-registry.sh

# Add to crontab (daily at 2am)
sudo crontab -e

# Add this line:
0 2 * * * /usr/local/bin/backup-word-registry.sh >> /var/log/word-registry-backup.log 2>&1
```

## Production Checklist

Before going live:

- [ ] Domain DNS pointed to droplet IP
- [ ] SSL certificate installed and working
- [ ] Stripe live keys configured
- [ ] Stripe webhook endpoint configured
- [ ] Database backups scheduled
- [ ] Firewall enabled and configured
- [ ] Services set to start on boot
- [ ] CORS configured for production domain
- [ ] Environment variables set to production
- [ ] Test complete purchase flow with real card
- [ ] Monitoring setup (optional: DigitalOcean monitoring, Sentry, etc.)

## Troubleshooting

### Backend won't start

```bash
# Check logs
sudo journalctl -u word-registry-backend -n 50

# Common issues:
# - Database connection (check DATABASE_URL)
# - Port already in use (check with: sudo lsof -i :8000)
# - Missing dependencies (pip install -r requirements.txt)
```

### Frontend won't start

```bash
# Check logs
sudo journalctl -u word-registry-frontend -n 50

# Common issues:
# - Build failed (run: npm run build)
# - Port already in use (check with: sudo lsof -i :3000)
# - Missing .env.local file
```

### Nginx errors

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Common issues:
# - Syntax errors in config
# - Port conflicts
# - SSL certificate issues
```

### Database connection issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U wordregistry_user -d word_registry -h localhost

# Check pg_hba.conf allows local connections
```

## Scaling Considerations

### Add Redis (Optional but Recommended)

```bash
# Install Redis
sudo apt install redis-server -y

# Configure Redis
sudo nano /etc/redis/redis.conf
# Set: supervised systemd

# Restart Redis
sudo systemctl restart redis

# Update backend .env
REDIS_URL=redis://localhost:6379

# Restart backend
sudo systemctl restart word-registry-backend
```

### Increase Workers

For better performance, increase uvicorn workers:

```bash
sudo nano /etc/systemd/system/word-registry-backend.service

# Change:
ExecStart=/var/www/word-registry/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart word-registry-backend
```

## Cost Estimate

**Monthly costs:**
- DigitalOcean Droplet: $12-24/month
- Domain: ~$12/year
- SSL: Free (Let's Encrypt)
- Stripe fees: 2.9% + $0.30 per transaction

**Total:** ~$13-25/month + transaction fees

## Support

For issues:
- DigitalOcean Docs: https://docs.digitalocean.com
- Stripe Docs: https://stripe.com/docs
- Project Issues: https://github.com/yourusername/word-registry/issues
