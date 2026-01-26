# Pre-Deployment Checklist

Complete this checklist before deploying to production.

## ☁️ Infrastructure Setup

### DigitalOcean Droplet
- [ ] Droplet created (Ubuntu 22.04 LTS, 4GB RAM recommended)
- [ ] SSH key added to droplet
- [ ] Droplet IP address noted
- [ ] Firewall enabled (UFW)

### Domain and DNS
- [ ] Domain purchased
- [ ] DNS A record points to droplet IP
- [ ] DNS propagated (check with `dig yourdomain.com`)
- [ ] www subdomain configured (optional)

## 🔐 Accounts and Keys

### Stripe
- [ ] Stripe account created
- [ ] Business information completed in Stripe dashboard
- [ ] Live mode enabled in Stripe dashboard
- [ ] **Test keys** obtained (for initial testing)
  - [ ] Test Secret Key (`sk_test_...`)
  - [ ] Test Publishable Key (`pk_test_...`)
- [ ] **Live keys** ready (for production)
  - [ ] Live Secret Key (`sk_live_...`)
  - [ ] Live Publishable Key (`pk_live_...`)
- [ ] Payment methods enabled (cards, Apple Pay, Google Pay)
- [ ] Email for receipts configured

### Database
- [ ] Strong database password generated (use password manager)
- [ ] Database password saved securely

### SSL
- [ ] Email address for Let's Encrypt notifications ready

## 📦 Code Repository

### GitHub
- [ ] Repository created on GitHub
- [ ] Code pushed to main/master branch
- [ ] Repository is private (recommended) or public
- [ ] Deployment keys configured (if private repo)

### Environment Files
- [ ] `.env` files NOT committed to repository
- [ ] `.env.example` files are up to date
- [ ] `.gitignore` includes `.env` and `.env.local`

## ⚙️ Configuration Review

### Backend Configuration (`backend/.env`)
Review the following values:
- [ ] `DATABASE_URL` - Will be set during deployment
- [ ] `STRIPE_SECRET_KEY` - Start with test, switch to live when ready
- [ ] `STRIPE_PUBLISHABLE_KEY` - Must match secret key (test or live)
- [ ] `STRIPE_WEBHOOK_SECRET` - Will configure after deployment
- [ ] `CORS_ORIGINS` - Set to your production domain (not `*`)
- [ ] `APP_ENV` - Set to `production`
- [ ] `DEBUG` - Set to `False`
- [ ] `RATE_LIMIT_ENABLED` - Set to `True`

Example production `backend/.env`:
```env
DATABASE_URL=postgresql://wordregistry_user:SECURE_PASSWORD@localhost:5432/word_registry
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
APP_ENV=production
DEBUG=False
RATE_LIMIT_ENABLED=True
REDIS_URL=
```

### Frontend Configuration (`frontend/.env.local`)
Review the following values:
- [ ] `NEXT_PUBLIC_API_URL` - Set to your production domain with `/api`
- [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` - Must match backend (test or live)

Example production `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

### Nginx Configuration
- [ ] Domain name updated in `nginx.conf`
- [ ] SSL certificate paths configured
- [ ] Rate limiting configured
- [ ] CORS headers match backend configuration

## 🧪 Local Testing

### Backend
- [ ] All tests pass (if you have tests)
- [ ] Backend starts without errors locally
- [ ] Health check endpoint works: `http://localhost:8000/health`
- [ ] Can create a word purchase with test card
- [ ] Word lockout mechanism works

### Frontend
- [ ] Frontend builds successfully: `npm run build`
- [ ] Frontend runs in production mode: `npm run start`
- [ ] All pages load without errors
- [ ] Search functionality works
- [ ] Word detail pages display correctly
- [ ] Countdown timers work
- [ ] Leaderboards load

### Stripe Integration (Test Mode)
- [ ] Can reach payment form
- [ ] Test card `4242 4242 4242 4242` works
- [ ] Payment success flow works end-to-end
- [ ] Word ownership transfers after payment
- [ ] Payment intent errors handled gracefully
- [ ] 3D Secure test card works (`4000 0025 0000 3155`)

## 🚀 Deployment Steps

### 1. Run Setup Script
- [ ] Downloaded `setup-server.sh` to droplet
- [ ] Made script executable: `chmod +x setup-server.sh`
- [ ] Ran script as root: `sudo ./setup-server.sh`
- [ ] Provided all required information during setup

### 2. Verify Services
- [ ] Backend service running: `sudo systemctl status word-registry-backend`
- [ ] Frontend service running: `sudo systemctl status word-registry-frontend`
- [ ] Nginx running: `sudo systemctl status nginx`
- [ ] PostgreSQL running: `sudo systemctl status postgresql`

### 3. SSL Certificate
- [ ] SSL certificate obtained via Let's Encrypt
- [ ] HTTPS redirect working (HTTP → HTTPS)
- [ ] No browser SSL warnings
- [ ] Certificate auto-renewal configured

### 4. Firewall
- [ ] UFW enabled: `sudo ufw status`
- [ ] SSH allowed (port 22)
- [ ] HTTP allowed (port 80)
- [ ] HTTPS allowed (port 443)
- [ ] All other ports blocked

## 🔗 External Services

### Stripe Webhook
- [ ] Webhook endpoint created in Stripe dashboard
- [ ] Webhook URL: `https://yourdomain.com/api/payment/webhook`
- [ ] Events selected: `payment_intent.succeeded`, `payment_intent.payment_failed`
- [ ] Webhook signing secret copied
- [ ] Webhook secret added to `backend/.env`
- [ ] Backend restarted after adding webhook secret
- [ ] Test webhook delivery successful

### DNS Verification
- [ ] Domain resolves to droplet IP: `dig yourdomain.com`
- [ ] www subdomain resolves (if configured): `dig www.yourdomain.com`
- [ ] No DNS propagation delays (wait 24-48 hours if needed)

## ✅ Post-Deployment Testing

### Basic Functionality
- [ ] Homepage loads: `https://yourdomain.com`
- [ ] Search works
- [ ] Random word button works
- [ ] Leaderboards load
- [ ] Word detail page loads
- [ ] Countdown timers work
- [ ] Transaction history displays

### Purchase Flow (Test Mode First!)
- [ ] Can click "Claim" on available word
- [ ] Purchase modal opens
- [ ] Can enter name and message
- [ ] Acknowledgment checkbox works
- [ ] "Continue to Payment" works
- [ ] Stripe payment form loads
- [ ] Test card payment succeeds: `4242 4242 4242 4242`
- [ ] Word ownership transfers
- [ ] Lockout timer starts
- [ ] Transaction appears in history

### Error Handling
- [ ] Locked word shows locked status
- [ ] Can't purchase locked word
- [ ] Invalid card shows error
- [ ] Content validation works (URLs blocked)
- [ ] Rate limiting works (test with script)

### Performance
- [ ] Pages load in < 3 seconds
- [ ] API responses in < 500ms
- [ ] No console errors in browser
- [ ] No 500 errors in server logs

### Security
- [ ] HTTPS enforced (no HTTP access)
- [ ] Security headers present (check with https://securityheaders.com)
- [ ] CORS configured correctly (only your domain allowed)
- [ ] No sensitive data in client-side code
- [ ] Database credentials not exposed

## 🎯 Go-Live Checklist

### Switch to Live Stripe Keys
- [ ] Test mode fully validated
- [ ] Ready to accept real payments
- [ ] Update `STRIPE_SECRET_KEY` to `sk_live_...` in `backend/.env`
- [ ] Update `STRIPE_PUBLISHABLE_KEY` to `pk_live_...` in `backend/.env`
- [ ] Update `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` to `pk_live_...` in `frontend/.env.local`
- [ ] Update Stripe webhook to use live mode endpoint
- [ ] Update `STRIPE_WEBHOOK_SECRET` with live mode secret
- [ ] Restart backend: `sudo systemctl restart word-registry-backend`
- [ ] Restart frontend: `sudo systemctl restart word-registry-frontend`
- [ ] Test with real card (make a small test purchase)
- [ ] Verify real money is processed (check Stripe dashboard)

### Monitoring
- [ ] Error monitoring setup (Sentry, LogRocket, etc.) - optional
- [ ] Uptime monitoring configured (UptimeRobot, Pingdom, etc.) - optional
- [ ] DigitalOcean monitoring enabled
- [ ] Backup cron job running: `sudo crontab -l`
- [ ] Test backup restoration

### Documentation
- [ ] Team knows how to deploy updates: `./deploy.sh`
- [ ] Emergency rollback procedure documented
- [ ] Contact information updated
- [ ] Stripe dashboard access shared with team

### Legal/Compliance
- [ ] Terms of Service page (if required)
- [ ] Privacy Policy page (if required)
- [ ] Cookie consent working
- [ ] GDPR compliance reviewed (if applicable)
- [ ] Stripe compliance requirements met

## 📱 Communication

### Announcement
- [ ] Social media announcement ready
- [ ] Email list notified (if applicable)
- [ ] Launch blog post ready (optional)

### Support
- [ ] Support email configured
- [ ] Support workflow documented
- [ ] Team trained on common issues

## 🎉 Launch!

**Final checks before launch:**
1. [ ] All items above completed
2. [ ] Test purchase with real card successful
3. [ ] All team members notified
4. [ ] Monitoring dashboards open
5. [ ] Ready to handle support requests

**Launch sequence:**
1. [ ] Switch to live Stripe keys (if not already done)
2. [ ] Restart services
3. [ ] Make final test purchase
4. [ ] Announce launch
5. [ ] Monitor for first hour
6. [ ] Celebrate! 🎊

## 📋 Post-Launch

**First 24 Hours:**
- [ ] Monitor error logs closely
- [ ] Check Stripe dashboard for payments
- [ ] Respond to user feedback
- [ ] Monitor server resources (CPU, memory, disk)

**First Week:**
- [ ] Review all transactions
- [ ] Check webhook delivery success rate
- [ ] Optimize performance if needed
- [ ] Address any user-reported issues

**First Month:**
- [ ] Review backup strategy
- [ ] Optimize database if needed
- [ ] Consider scaling if traffic high
- [ ] Review security practices

## 🆘 Rollback Plan

If something goes wrong after launch:

1. **Immediate issues:**
   ```bash
   cd /var/www/word-registry
   git log --oneline -10  # Find previous stable commit
   git checkout <previous-commit>
   ./deploy.sh
   ```

2. **Database issues:**
   ```bash
   # Restore from backup
   gunzip < /var/backups/word-registry/db_backup_TIMESTAMP.sql.gz | sudo -u postgres psql word_registry
   ```

3. **Service issues:**
   ```bash
   # Restart all services
   sudo systemctl restart word-registry-backend
   sudo systemctl restart word-registry-frontend
   sudo systemctl reload nginx
   ```

4. **Critical emergency:**
   - Put up maintenance page
   - Investigate issue in staging environment
   - Communicate with users
   - Fix and redeploy when ready

## 📞 Emergency Contacts

- **Developer On-Call:** [Your phone/email]
- **DigitalOcean Support:** https://support.digitalocean.com
- **Stripe Support:** https://support.stripe.com
- **Domain Registrar:** [Your registrar's support]

---

**Remember:** It's okay to deploy to test mode first, validate everything works, then switch to live mode when ready!

**Good luck with your deployment! 🚀**
