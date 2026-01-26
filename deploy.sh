#!/bin/bash

##############################################################################
# Word Registry Deployment Script
# Performs zero-downtime deployment on DigitalOcean droplet
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/var/www/word-registry"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
BACKUP_DIR="/var/backups/word-registry/deployments"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Error handler
handle_error() {
    log_error "Deployment failed at line $1"
    log_warning "Consider rolling back if services are down"
    exit 1
}

trap 'handle_error $LINENO' ERR

##############################################################################
# Pre-deployment checks
##############################################################################

log_info "Starting deployment at $(date)"
log_info "Timestamp: $TIMESTAMP"

# Check if running as correct user
if [ "$USER" != "wordregistry" ]; then
    log_error "This script must be run as the wordregistry user"
    exit 1
fi

# Check if we're in the right directory
if [ ! -d "$APP_DIR" ]; then
    log_error "Application directory not found: $APP_DIR"
    exit 1
fi

cd $APP_DIR

# Check services are running before we start
log_info "Checking service status..."
if ! systemctl is-active --quiet word-registry-backend; then
    log_warning "Backend service is not running"
fi
if ! systemctl is-active --quiet word-registry-frontend; then
    log_warning "Frontend service is not running"
fi

##############################################################################
# Create backup
##############################################################################

log_info "Creating backup..."
mkdir -p $BACKUP_DIR

# Backup current code
tar -czf "$BACKUP_DIR/code_backup_$TIMESTAMP.tar.gz" \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='.next' \
    --exclude='__pycache__' \
    . 2>/dev/null || log_warning "Backup creation had warnings"

# Backup database
log_info "Backing up database..."
sudo -u postgres pg_dump word_registry | gzip > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"

log_success "Backup created: $BACKUP_DIR/*_$TIMESTAMP.*"

##############################################################################
# Pull latest code
##############################################################################

log_info "Fetching latest code from git..."

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log_info "Current branch: $CURRENT_BRANCH"

# Get current commit hash (for rollback reference)
PREVIOUS_COMMIT=$(git rev-parse HEAD)
log_info "Previous commit: $PREVIOUS_COMMIT"

# Pull latest changes
git fetch origin
git pull origin $CURRENT_BRANCH

NEW_COMMIT=$(git rev-parse HEAD)
log_info "New commit: $NEW_COMMIT"

if [ "$PREVIOUS_COMMIT" = "$NEW_COMMIT" ]; then
    log_warning "No new changes to deploy"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment cancelled"
        exit 0
    fi
fi

##############################################################################
# Backend deployment
##############################################################################

log_info "Deploying backend..."

cd $BACKEND_DIR

# Activate virtual environment
source venv/bin/activate

# Check if requirements changed
if git diff --name-only $PREVIOUS_COMMIT $NEW_COMMIT | grep -q "backend/requirements.txt"; then
    log_info "requirements.txt changed, updating dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    log_info "No dependency changes detected"
fi

# Run database migrations (if you add alembic later)
# log_info "Running database migrations..."
# alembic upgrade head

# Warmup ML models (optional, helps with first request performance)
log_info "Warming up ML models..."
python warmup_ml.py || log_warning "ML warmup failed (not critical)"

# Test backend can start (quick syntax check)
log_info "Testing backend..."
timeout 5 python -c "from app.main import app; print('Backend import successful')" || {
    log_error "Backend has import errors!"
    exit 1
}

log_success "Backend prepared"

##############################################################################
# Frontend deployment
##############################################################################

log_info "Deploying frontend..."

cd $FRONTEND_DIR

# Check if package.json changed
if git diff --name-only $PREVIOUS_COMMIT $NEW_COMMIT | grep -q "frontend/package"; then
    log_info "package files changed, updating dependencies..."
    npm install
else
    log_info "No dependency changes detected"
fi

# Build frontend
log_info "Building frontend (this may take a minute)..."
npm run build

log_success "Frontend built"

##############################################################################
# Restart services (zero-downtime)
##############################################################################

log_info "Restarting services..."

# Restart backend (systemd handles graceful restart)
log_info "Restarting backend service..."
sudo systemctl restart word-registry-backend

# Wait for backend to be healthy
log_info "Waiting for backend to be healthy..."
sleep 3
for i in {1..10}; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend is healthy"
        break
    fi
    if [ $i -eq 10 ]; then
        log_error "Backend health check failed after 10 attempts"
        log_error "Check logs: sudo journalctl -u word-registry-backend -n 50"
        exit 1
    fi
    log_info "Waiting for backend... (attempt $i/10)"
    sleep 2
done

# Restart frontend
log_info "Restarting frontend service..."
sudo systemctl restart word-registry-frontend

# Wait for frontend to be healthy
log_info "Waiting for frontend to be healthy..."
sleep 3
for i in {1..10}; do
    if curl -sf http://localhost:3000 > /dev/null 2>&1; then
        log_success "Frontend is healthy"
        break
    fi
    if [ $i -eq 10 ]; then
        log_error "Frontend health check failed after 10 attempts"
        log_error "Check logs: sudo journalctl -u word-registry-frontend -n 50"
        exit 1
    fi
    log_info "Waiting for frontend... (attempt $i/10)"
    sleep 2
done

# Reload Nginx (graceful reload, no downtime)
log_info "Reloading Nginx..."
sudo nginx -t && sudo systemctl reload nginx

log_success "All services restarted successfully"

##############################################################################
# Post-deployment checks
##############################################################################

log_info "Running post-deployment checks..."

# Check service status
log_info "Service status:"
systemctl is-active word-registry-backend && log_success "  Backend: running" || log_error "  Backend: NOT running"
systemctl is-active word-registry-frontend && log_success "  Frontend: running" || log_error "  Frontend: NOT running"
systemctl is-active nginx && log_success "  Nginx: running" || log_error "  Nginx: NOT running"

# Test API endpoint
if curl -sf http://localhost:8000/api/leaderboard/stats > /dev/null 2>&1; then
    log_success "API endpoint responding"
else
    log_warning "API endpoint not responding (may be warming up)"
fi

# Show recent logs
log_info "Recent backend logs:"
sudo journalctl -u word-registry-backend -n 5 --no-pager

log_info "Recent frontend logs:"
sudo journalctl -u word-registry-frontend -n 5 --no-pager

##############################################################################
# Cleanup old backups
##############################################################################

log_info "Cleaning up old backups (keeping last 7 days)..."
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete 2>/dev/null || true
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete 2>/dev/null || true

##############################################################################
# Deployment complete
##############################################################################

log_success "=========================================="
log_success "Deployment completed successfully!"
log_success "=========================================="
log_info "Deployed commit: $NEW_COMMIT"
log_info "Backup location: $BACKUP_DIR/*_$TIMESTAMP.*"
log_info "Deployment time: $(date)"
log_info ""
log_info "To view logs:"
log_info "  Backend:  sudo journalctl -u word-registry-backend -f"
log_info "  Frontend: sudo journalctl -u word-registry-frontend -f"
log_info "  Nginx:    sudo tail -f /var/log/nginx/word-registry-error.log"
log_info ""
log_info "To rollback:"
log_info "  git checkout $PREVIOUS_COMMIT"
log_info "  ./deploy.sh"
log_info ""
log_success "Happy shipping! 🚀"
