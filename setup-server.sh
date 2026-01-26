#!/bin/bash

##############################################################################
# Word Registry Server Setup Script
# Automates initial setup on Ubuntu 22.04 DigitalOcean droplet
#
# Usage:
#   1. SSH into your droplet as root
#   2. wget https://raw.githubusercontent.com/yourusername/word-registry/main/setup-server.sh
#   3. chmod +x setup-server.sh
#   4. ./setup-server.sh
##############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

##############################################################################
# Welcome
##############################################################################

clear
echo "=========================================="
echo "  Word Registry Server Setup"
echo "  Ubuntu 22.04 LTS"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

# Confirm
read -p "This will set up the server from scratch. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Setup cancelled"
    exit 0
fi

##############################################################################
# Gather configuration
##############################################################################

log_info "Please provide the following information:"
echo ""

# Domain
read -p "Enter your domain name (e.g., wordregistry.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    log_error "Domain is required"
    exit 1
fi

# Database password
read -sp "Enter database password (will be hidden): " DB_PASSWORD
echo ""
if [ -z "$DB_PASSWORD" ]; then
    log_error "Database password is required"
    exit 1
fi

# Stripe keys (optional for initial setup)
echo ""
log_info "Stripe keys (you can add these later if needed):"
read -p "Stripe Secret Key (press Enter to skip): " STRIPE_SECRET
read -p "Stripe Publishable Key (press Enter to skip): " STRIPE_PUBLIC

# GitHub repository
echo ""
read -p "GitHub repository URL (e.g., https://github.com/user/repo.git): " GITHUB_REPO
if [ -z "$GITHUB_REPO" ]; then
    log_error "GitHub repository is required"
    exit 1
fi

# Email for Let's Encrypt
read -p "Email for Let's Encrypt SSL notifications: " LETSENCRYPT_EMAIL
if [ -z "$LETSENCRYPT_EMAIL" ]; then
    log_error "Email is required for SSL certificates"
    exit 1
fi

##############################################################################
# System update
##############################################################################

log_info "Updating system packages..."
apt update
apt upgrade -y
apt install -y software-properties-common curl wget git ufw

log_success "System updated"

##############################################################################
# Create application user
##############################################################################

log_info "Creating application user..."

if id "wordregistry" &>/dev/null; then
    log_warning "User wordregistry already exists"
else
    adduser --disabled-password --gecos "" wordregistry
    usermod -aG sudo wordregistry
    log_success "User wordregistry created"
fi

# Set up SSH for new user
if [ -d /root/.ssh ]; then
    rsync --archive --chown=wordregistry:wordregistry /root/.ssh /home/wordregistry/
    log_success "SSH keys copied to wordregistry user"
fi

##############################################################################
# Install Python 3.13
##############################################################################

log_info "Installing Python 3.13..."

add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install -y python3.13 python3.13-venv python3.13-dev python3-pip

python3.13 --version
log_success "Python 3.13 installed"

##############################################################################
# Install Node.js 20
##############################################################################

log_info "Installing Node.js 20..."

curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

node --version
npm --version
log_success "Node.js installed"

##############################################################################
# Install PostgreSQL
##############################################################################

log_info "Installing PostgreSQL..."

apt install -y postgresql postgresql-contrib

systemctl start postgresql
systemctl enable postgresql

log_success "PostgreSQL installed"

# Create database and user
log_info "Setting up database..."

sudo -u postgres psql <<EOF
CREATE DATABASE word_registry;
CREATE USER wordregistry_user WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE word_registry TO wordregistry_user;
\q
EOF

log_success "Database created"

##############################################################################
# Install Nginx
##############################################################################

log_info "Installing Nginx..."

apt install -y nginx

systemctl start nginx
systemctl enable nginx

log_success "Nginx installed"

##############################################################################
# Install Certbot
##############################################################################

log_info "Installing Certbot for SSL..."

apt install -y certbot python3-certbot-nginx

log_success "Certbot installed"

##############################################################################
# Clone repository
##############################################################################

log_info "Cloning repository..."

mkdir -p /var/www/word-registry
chown wordregistry:wordregistry /var/www/word-registry

sudo -u wordregistry git clone $GITHUB_REPO /var/www/word-registry

log_success "Repository cloned"

##############################################################################
# Backend setup
##############################################################################

log_info "Setting up backend..."

cd /var/www/word-registry/backend

# Create virtual environment
sudo -u wordregistry python3.13 -m venv venv

# Install dependencies
sudo -u wordregistry bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

# Create .env file
cat > .env <<EOF
DATABASE_URL=postgresql://wordregistry_user:$DB_PASSWORD@localhost:5432/word_registry
STRIPE_SECRET_KEY=$STRIPE_SECRET
STRIPE_PUBLISHABLE_KEY=$STRIPE_PUBLIC
STRIPE_WEBHOOK_SECRET=
RATE_LIMIT_ENABLED=True
REDIS_URL=
ENVIRONMENT=production
EOF

chown wordregistry:wordregistry .env
chmod 600 .env

# Initialize database
log_info "Initializing database..."
sudo -u wordregistry bash -c "source venv/bin/activate && python init_db.py"

# Import words
log_info "Importing words (this may take a minute)..."
sudo -u wordregistry bash -c "source venv/bin/activate && python import_words.py"

log_success "Backend setup complete"

##############################################################################
# Frontend setup
##############################################################################

log_info "Setting up frontend..."

cd /var/www/word-registry/frontend

# Install dependencies
sudo -u wordregistry npm install

# Create .env.local
cat > .env.local <<EOF
NEXT_PUBLIC_API_URL=https://$DOMAIN/api
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=$STRIPE_PUBLIC
EOF

chown wordregistry:wordregistry .env.local

# Build frontend
log_info "Building frontend (this may take a few minutes)..."
sudo -u wordregistry npm run build

log_success "Frontend setup complete"

##############################################################################
# Create systemd services
##############################################################################

log_info "Creating systemd services..."

# Backend service
cat > /etc/systemd/system/word-registry-backend.service <<EOF
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
EOF

# Frontend service
cat > /etc/systemd/system/word-registry-frontend.service <<EOF
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
EOF

# Reload systemd and enable services
systemctl daemon-reload
systemctl enable word-registry-backend
systemctl enable word-registry-frontend

log_success "Systemd services created"

##############################################################################
# Configure Nginx
##############################################################################

log_info "Configuring Nginx..."

# Copy nginx config
cp /var/www/word-registry/nginx.conf /etc/nginx/sites-available/word-registry

# Replace domain placeholder
sed -i "s/yourdomain.com/$DOMAIN/g" /etc/nginx/sites-available/word-registry

# Enable site
ln -sf /etc/nginx/sites-available/word-registry /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test configuration
nginx -t

log_success "Nginx configured"

##############################################################################
# Configure firewall
##############################################################################

log_info "Configuring firewall..."

ufw --force enable
ufw allow OpenSSH
ufw allow 'Nginx Full'

log_success "Firewall configured"

##############################################################################
# Start services
##############################################################################

log_info "Starting services..."

systemctl start word-registry-backend
systemctl start word-registry-frontend
systemctl reload nginx

# Wait for services to start
sleep 5

# Check status
if systemctl is-active --quiet word-registry-backend; then
    log_success "Backend service started"
else
    log_error "Backend service failed to start"
fi

if systemctl is-active --quiet word-registry-frontend; then
    log_success "Frontend service started"
else
    log_error "Frontend service failed to start"
fi

##############################################################################
# SSL certificate
##############################################################################

log_info "Obtaining SSL certificate..."

certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email $LETSENCRYPT_EMAIL --redirect

log_success "SSL certificate obtained"

##############################################################################
# Setup backup cron
##############################################################################

log_info "Setting up automatic backups..."

cat > /usr/local/bin/backup-word-registry.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/word-registry"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
sudo -u postgres pg_dump word_registry | gzip > $BACKUP_DIR/word_registry_$DATE.sql.gz
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup-word-registry.sh

# Add to crontab (daily at 2am)
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-word-registry.sh >> /var/log/word-registry-backup.log 2>&1") | crontab -

log_success "Automatic backups configured"

##############################################################################
# Make deploy script executable
##############################################################################

chmod +x /var/www/word-registry/deploy.sh
chown wordregistry:wordregistry /var/www/word-registry/deploy.sh

##############################################################################
# Complete
##############################################################################

log_success "=========================================="
log_success "Server setup complete!"
log_success "=========================================="
echo ""
log_info "Your application is now running at:"
log_success "  https://$DOMAIN"
echo ""
log_info "Service status:"
systemctl status word-registry-backend --no-pager | grep "Active:"
systemctl status word-registry-frontend --no-pager | grep "Active:"
echo ""
log_info "To deploy updates in the future:"
log_info "  1. SSH as wordregistry user: ssh wordregistry@$DOMAIN"
log_info "  2. cd /var/www/word-registry"
log_info "  3. ./deploy.sh"
echo ""
log_info "To view logs:"
log_info "  Backend:  sudo journalctl -u word-registry-backend -f"
log_info "  Frontend: sudo journalctl -u word-registry-frontend -f"
echo ""
log_info "Next steps:"
log_info "  1. Configure Stripe webhook at: https://dashboard.stripe.com/webhooks"
log_info "     Webhook URL: https://$DOMAIN/api/payment/webhook"
log_info "  2. Test the application at: https://$DOMAIN"
log_info "  3. Update CORS settings in backend/app/main.py if needed"
echo ""
log_warning "IMPORTANT: Save your database password securely!"
log_warning "Database password: $DB_PASSWORD"
echo ""
log_success "Happy shipping! 🚀"
