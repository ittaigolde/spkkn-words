# Deployment Quick Reference

Quick commands and tips for managing your deployed Word Registry application.

## Initial Setup

```bash
# 1. Download setup script to your droplet
wget https://raw.githubusercontent.com/yourusername/word-registry/main/setup-server.sh

# 2. Make it executable
chmod +x setup-server.sh

# 3. Run as root
sudo ./setup-server.sh
```

The setup script will prompt you for:
- Domain name
- Database password
- Stripe keys (optional)
- GitHub repository URL
- Email for SSL certificates

## Common Commands

### Service Management

```bash
# Check service status
sudo systemctl status word-registry-backend
sudo systemctl status word-registry-frontend
sudo systemctl status nginx

# Start services
sudo systemctl start word-registry-backend
sudo systemctl start word-registry-frontend

# Stop services
sudo systemctl stop word-registry-backend
sudo systemctl stop word-registry-frontend

# Restart services
sudo systemctl restart word-registry-backend
sudo systemctl restart word-registry-frontend

# Restart services gracefully (recommended)
sudo systemctl reload word-registry-backend
sudo systemctl reload word-registry-frontend

# Reload Nginx (no downtime)
sudo nginx -t && sudo systemctl reload nginx
```

### View Logs

```bash
# Backend logs (live tail)
sudo journalctl -u word-registry-backend -f

# Frontend logs (live tail)
sudo journalctl -u word-registry-frontend -f

# Backend logs (last 100 lines)
sudo journalctl -u word-registry-backend -n 100

# Frontend logs (last 100 lines)
sudo journalctl -u word-registry-frontend -n 100

# Nginx access logs
sudo tail -f /var/log/nginx/word-registry-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/word-registry-error.log

# All logs since 1 hour ago
sudo journalctl -u word-registry-backend --since "1 hour ago"
```

### Deployments

```bash
# Deploy latest changes (zero downtime)
cd /var/www/word-registry
./deploy.sh

# Deploy specific commit/branch
cd /var/www/word-registry
git checkout <commit-hash-or-branch>
./deploy.sh
```

### Database Operations

```bash
# Backup database
sudo -u postgres pg_dump word_registry | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore database
gunzip < backup_20260126.sql.gz | sudo -u postgres psql word_registry

# Connect to database
sudo -u postgres psql word_registry

# View database size
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('word_registry'));"

# View table sizes
sudo -u postgres psql word_registry -c "\dt+"
```

### SSL Certificate Management

```bash
# Renew SSL certificate (auto-renewed by cron)
sudo certbot renew

# Test renewal (dry run)
sudo certbot renew --dry-run

# View certificate expiration
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal
```

### Environment Configuration

```bash
# Edit backend environment
sudo nano /var/www/word-registry/backend/.env

# Edit frontend environment
sudo nano /var/www/word-registry/frontend/.env.local

# After editing, restart services
sudo systemctl restart word-registry-backend
sudo systemctl restart word-registry-frontend
```

### Update Stripe Webhook Secret

```bash
# Edit backend .env
sudo nano /var/www/word-registry/backend/.env

# Add/update this line:
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here

# Restart backend
sudo systemctl restart word-registry-backend
```

### Nginx Configuration

```bash
# Edit Nginx config
sudo nano /etc/nginx/sites-available/word-registry

# Test configuration
sudo nginx -t

# Reload Nginx (no downtime)
sudo systemctl reload nginx

# View Nginx status
sudo systemctl status nginx
```

### Monitoring

```bash
# Check disk space
df -h

# Check memory usage
free -h

# Check CPU usage
top

# Check running processes
ps aux | grep -E 'uvicorn|node|nginx'

# Check port usage
sudo lsof -i :80    # Nginx HTTP
sudo lsof -i :443   # Nginx HTTPS
sudo lsof -i :8000  # Backend
sudo lsof -i :3000  # Frontend
sudo lsof -i :5432  # PostgreSQL

# Check system load
uptime
```

### Firewall

```bash
# View firewall status
sudo ufw status

# View firewall rules
sudo ufw status numbered

# Allow a specific IP
sudo ufw allow from 1.2.3.4

# Block a specific IP
sudo ufw deny from 1.2.3.4

# Delete a rule
sudo ufw delete <number>
```

## Troubleshooting

### Backend Won't Start

```bash
# Check logs for errors
sudo journalctl -u word-registry-backend -n 50

# Test backend manually
cd /var/www/word-registry/backend
source venv/bin/activate
python -c "from app.main import app; print('Import successful')"

# Check if port is in use
sudo lsof -i :8000

# Kill process on port 8000 (if needed)
sudo kill $(sudo lsof -t -i:8000)
```

### Frontend Won't Start

```bash
# Check logs for errors
sudo journalctl -u word-registry-frontend -n 50

# Test frontend manually
cd /var/www/word-registry/frontend
npm run build
npm run start

# Check if port is in use
sudo lsof -i :3000
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -c "\l"

# Check connection from app user
psql -U wordregistry_user -d word_registry -h localhost

# View active connections
sudo -u postgres psql word_registry -c "SELECT * FROM pg_stat_activity;"
```

### Out of Memory

```bash
# Check memory usage
free -h

# Check largest processes
ps aux --sort=-%mem | head -10

# Restart services to free memory
sudo systemctl restart word-registry-backend
sudo systemctl restart word-registry-frontend
```

### SSL Certificate Issues

```bash
# Check certificate validity
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal

# Check Nginx SSL config
sudo nginx -t
```

## Performance Tuning

### Increase Backend Workers

```bash
# Edit backend service
sudo nano /etc/systemd/system/word-registry-backend.service

# Change --workers value:
ExecStart=.../uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart word-registry-backend
```

### Add Redis for Caching

```bash
# Install Redis
sudo apt install redis-server -y

# Start and enable Redis
sudo systemctl start redis
sudo systemctl enable redis

# Update backend .env
sudo nano /var/www/word-registry/backend/.env

# Add this line:
REDIS_URL=redis://localhost:6379

# Restart backend
sudo systemctl restart word-registry-backend
```

### Enable Nginx Caching

Edit `/etc/nginx/sites-available/word-registry` and add caching directives (already included in nginx.conf).

## Rollback Procedure

```bash
# View recent commits
cd /var/www/word-registry
git log --oneline -10

# Rollback to specific commit
git checkout <previous-commit-hash>

# Deploy the old version
./deploy.sh

# OR restore from backup
cd /var/backups/word-registry/deployments
# Find your backup: ls -lh
tar -xzf code_backup_TIMESTAMP.tar.gz -C /var/www/word-registry/
cd /var/www/word-registry
./deploy.sh
```

## Backup and Restore

### Manual Backup

```bash
# Backup everything
sudo tar -czf /var/backups/word-registry-full-$(date +%Y%m%d).tar.gz \
  --exclude='node_modules' \
  --exclude='venv' \
  --exclude='.next' \
  /var/www/word-registry

# Backup database
sudo -u postgres pg_dump word_registry | gzip > /var/backups/word-registry-db-$(date +%Y%m%d).sql.gz
```

### Restore from Backup

```bash
# Restore code
sudo tar -xzf /var/backups/word-registry-full-20260126.tar.gz -C /

# Restore database
gunzip < /var/backups/word-registry-db-20260126.sql.gz | sudo -u postgres psql word_registry

# Restart services
sudo systemctl restart word-registry-backend
sudo systemctl restart word-registry-frontend
```

## Security

### Update System Packages

```bash
# Update all packages
sudo apt update
sudo apt upgrade -y

# Check for security updates
sudo apt list --upgradable
```

### Change Database Password

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Change password
ALTER USER wordregistry_user WITH PASSWORD 'new_secure_password';
\q

# Update backend .env
sudo nano /var/www/word-registry/backend/.env

# Update DATABASE_URL with new password
# Restart backend
sudo systemctl restart word-registry-backend
```

### View Failed Login Attempts

```bash
# View failed SSH attempts
sudo grep "Failed password" /var/log/auth.log | tail -20

# View blocked IPs (if using fail2ban)
sudo fail2ban-client status sshd
```

## Monitoring Setup (Optional)

### Install Netdata (Real-time Monitoring)

```bash
# Install Netdata
bash <(curl -Ss https://get.netdata.cloud/kickstart.sh)

# Access at: http://your-ip:19999
```

### Setup DigitalOcean Monitoring

Enable monitoring in your droplet settings on DigitalOcean dashboard.

## Useful File Locations

```
Application:       /var/www/word-registry/
Backend code:      /var/www/word-registry/backend/
Frontend code:     /var/www/word-registry/frontend/
Backend .env:      /var/www/word-registry/backend/.env
Frontend .env:     /var/www/word-registry/frontend/.env.local

Systemd services:  /etc/systemd/system/word-registry-*.service
Nginx config:      /etc/nginx/sites-available/word-registry
Nginx logs:        /var/log/nginx/
SSL certificates:  /etc/letsencrypt/live/yourdomain.com/

Backups:          /var/backups/word-registry/
Database backups: /var/backups/word-registry/*.sql.gz
Code backups:     /var/backups/word-registry/deployments/
```

## Emergency Contacts

- **DigitalOcean Support:** support.digitalocean.com
- **Stripe Support:** support.stripe.com
- **Domain Registrar:** (your registrar's support)
- **On-Call Developer:** (your contact info)

## Health Check URLs

- **Frontend:** https://yourdomain.com
- **Backend API:** https://yourdomain.com/api/health
- **API Docs:** https://yourdomain.com/docs
- **Nginx Status:** http://yourdomain.com (should redirect to HTTPS)

## Regular Maintenance

**Daily:**
- Check error logs for issues
- Monitor disk space

**Weekly:**
- Review backup logs
- Check SSL certificate expiration (90 days)
- Review system updates

**Monthly:**
- Update system packages
- Review and rotate logs
- Test backup restoration
- Review Stripe webhook delivery logs

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/word-registry/issues
- Email: support@yourdomain.com
