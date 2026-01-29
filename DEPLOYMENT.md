# Deployment Guide - Word Registry

This guide covers deploying the Word Registry application to production using Vercel (frontend) and Railway (backend).

## Overview

- **Frontend**: Next.js app hosted on Vercel
- **Backend**: FastAPI app + PostgreSQL database hosted on Railway
- **Mode**: Demo mode with Stripe test keys for verification

## Prerequisites

- GitHub account
- Vercel account (sign up at vercel.com)
- Railway account (sign up at railway.app)
- Stripe test API keys

---

## Part 1: Deploy Backend to Railway

### Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app) and sign in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Connect your GitHub account and select this repository
5. Railway will detect the Dockerfile automatically

### Step 2: Add PostgreSQL Database

1. In your Railway project, click **"New"** → **"Database"** → **"PostgreSQL"**
2. Railway will automatically create a database and set `DATABASE_URL` environment variable

### Step 3: Configure Environment Variables

In Railway project settings → Variables tab, add these variables:

```bash
# Stripe (use test keys for demo)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_... (optional for demo)

# Application
APP_ENV=production
DEBUG=False

# CORS - Add your Vercel domain after deployment
CORS_ORIGINS=https://your-app.vercel.app

# Admin
ADMIN_TOTP_SECRET=your_totp_secret_here
ADMIN_SETUP_ENABLED=False

# Moderation
REPORT_THRESHOLD=10
RATE_LIMIT_ENABLED=True
```

### Step 4: Initialize Database

1. Wait for the backend to deploy
2. In Railway, open the backend service
3. Click **"Settings"** → **"Service"** → **"Custom Start Command"**
4. Temporarily change to: `python init_db.py && python migrate_add_moderation.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. This will create tables on first deploy
6. After successful deploy, revert to default command or use: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 5: Import Words (Optional)

To import the 20k word list:

1. In Railway, click on your backend service
2. Go to **"Settings"** → **"Variables"**
3. Note your `DATABASE_URL`
4. Locally, run:
   ```bash
   cd backend
   # Set DATABASE_URL to your Railway PostgreSQL URL
   ./venv/Scripts/python.exe import_words.py
   ```

### Step 6: Note Your Backend URL

- Railway will provide a URL like: `https://your-app-name.railway.app`
- Copy this URL for the frontend configuration

---

## Part 2: Deploy Frontend to Vercel

### Step 1: Create Vercel Project

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. Vercel will detect it's a Next.js app
5. Set **Root Directory** to `frontend`

### Step 2: Configure Environment Variables

In Vercel project settings → Environment Variables, add:

```bash
# Backend API URL (from Railway)
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app

# Stripe Publishable Key (test key)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### Step 3: Deploy

1. Click **"Deploy"**
2. Wait for build to complete (3-5 minutes)
3. Note your frontend URL: `https://your-app.vercel.app`

### Step 4: Update Backend CORS

1. Go back to Railway
2. Update the `CORS_ORIGINS` environment variable to include your Vercel URL:
   ```
   CORS_ORIGINS=https://your-app.vercel.app
   ```
3. Railway will automatically redeploy

---

## Part 3: Configure Stripe Webhook (Optional for Demo)

For full functionality in demo mode:

1. In Stripe Dashboard → **Developers** → **Webhooks**
2. Click **"Add endpoint"**
3. Set endpoint URL: `https://your-backend-url.railway.app/api/payment/webhook`
4. Select events: `payment_intent.succeeded`, `payment_intent.payment_failed`
5. Copy the webhook signing secret
6. Add to Railway environment variables as `STRIPE_WEBHOOK_SECRET`

---

## Part 4: Setup Admin Access

### First-Time Admin Setup

1. **Temporarily enable setup page**: Set `ADMIN_SETUP_ENABLED=True` in Railway
2. Visit: `https://your-app.vercel.app/admin/setup`
3. Scan QR code with Google Authenticator or Authy
4. Save the secret key securely
5. **IMPORTANT**: Set `ADMIN_SETUP_ENABLED=False` in Railway immediately after setup

### Admin Login

1. Visit: `https://your-app.vercel.app/admin/login`
2. Enter 6-digit code from authenticator app
3. Access dashboard and content moderation

---

## Part 5: Verification Checklist

Before submitting to Stripe for review:

### Required Pages
- ✅ Home page with clear explanation
- ✅ Word purchase flow working
- ✅ Test payments with Stripe test cards
- ✅ Lockout timer displaying correctly
- ✅ Leaderboards showing data

### Optional (Recommended for Stripe)
- [ ] Terms of Service page
- [ ] Privacy Policy page
- [ ] Contact/Support information
- [ ] Refund policy (if applicable)
- [ ] Demo mode banner

### Testing Checklist
- [ ] Buy a word with test card (4242 4242 4242 4242)
- [ ] Verify lockout timer counts down
- [ ] Steal a word after timer expires
- [ ] Test message reporting
- [ ] Test admin moderation panel
- [ ] Verify leaderboards update

---

## Environment Variables Quick Reference

### Backend (Railway)
```bash
DATABASE_URL=<auto-generated>
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
APP_ENV=production
DEBUG=False
CORS_ORIGINS=https://your-app.vercel.app
ADMIN_TOTP_SECRET=...
ADMIN_SETUP_ENABLED=False
REPORT_THRESHOLD=10
RATE_LIMIT_ENABLED=True
```

### Frontend (Vercel)
```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

---

## Troubleshooting

### Backend won't start
- Check Railway logs for errors
- Verify DATABASE_URL is set
- Ensure all required env vars are present

### Frontend can't connect to backend
- Verify NEXT_PUBLIC_API_URL is correct
- Check CORS_ORIGINS in backend includes frontend URL
- Check Railway backend is running (look for green status)

### Database tables missing
- Run init_db.py and migrate_add_moderation.py
- Check Railway logs for migration errors

### Stripe payments fail
- Verify you're using test keys (sk_test_ and pk_test_)
- Check backend logs for errors
- Ensure Stripe publishable key matches secret key

---

## Costs

**Current Setup (Free Tier)**:
- Vercel: Free (100GB bandwidth, 100 builds/month)
- Railway: Free tier available ($5 credit/month, ~500 hours runtime)
- PostgreSQL: Included in Railway free tier (limited storage)

**If you exceed free tier**:
- Railway: ~$5-10/month for backend + database
- Vercel: Hobby plan $20/month (if needed)

---

## Next Steps After Deployment

1. Test all functionality on production URLs
2. Add Terms/Privacy pages if needed for Stripe
3. Submit to Stripe for review with production URL
4. Monitor Railway and Vercel dashboards for errors
5. Set up custom domain (optional)

---

## Support

- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- Report issues: Create an issue in the GitHub repo
