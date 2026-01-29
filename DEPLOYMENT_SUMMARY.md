# Deployment Configuration Summary

All deployment files have been created for deploying to Vercel + Railway.

## Files Created

### Backend (Railway)
- ✅ `backend/Dockerfile` - Containerizes the FastAPI application
- ✅ `backend/.dockerignore` - Excludes unnecessary files from Docker image
- ✅ `backend/railway.json` - Railway-specific configuration
- ✅ `backend/.env.production.template` - Template for production environment variables

### Frontend (Vercel)
- ✅ `frontend/vercel.json` - Vercel deployment configuration
- ✅ `frontend/.env.production.template` - Template for frontend environment variables
- ✅ `frontend/components/DemoBanner.tsx` - Demo mode banner component

### Documentation
- ✅ `DEPLOYMENT.md` - Complete step-by-step deployment guide

## Quick Start

### 1. Push to GitHub
```bash
git add .
git commit -m "Add deployment configuration for Vercel and Railway"
git push origin master
```

### 2. Deploy Backend (Railway)
1. Go to https://railway.app
2. Create new project from GitHub repo
3. Add PostgreSQL database
4. Set environment variables from `backend/.env.production.template`
5. Deploy automatically happens

### 3. Deploy Frontend (Vercel)
1. Go to https://vercel.com
2. Import GitHub repo
3. Set root directory to `frontend`
4. Add environment variables from `frontend/.env.production.template`
5. Deploy

### 4. Configure CORS
Update Railway's `CORS_ORIGINS` with your Vercel URL

## Environment Variables Checklist

### Backend (Railway)
- [ ] `DATABASE_URL` (auto-generated)
- [ ] `STRIPE_SECRET_KEY` (sk_test_...)
- [ ] `STRIPE_PUBLISHABLE_KEY` (pk_test_...)
- [ ] `CORS_ORIGINS` (Vercel URL)
- [ ] `ADMIN_TOTP_SECRET` (from dev environment)
- [ ] `APP_ENV=production`
- [ ] `DEBUG=False`
- [ ] `ADMIN_SETUP_ENABLED=False`
- [ ] `REPORT_THRESHOLD=10`
- [ ] `RATE_LIMIT_ENABLED=True`

### Frontend (Vercel)
- [ ] `NEXT_PUBLIC_API_URL` (Railway backend URL)
- [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` (pk_test_...)
- [ ] `NEXT_PUBLIC_DEMO_MODE=true`

## Demo Mode Features

The demo banner will appear when `NEXT_PUBLIC_DEMO_MODE=true`:
- Shows yellow banner at top of page
- Displays test card information
- Helps reviewers understand it's a demo

## Testing After Deployment

1. Visit your frontend URL
2. Buy a word with test card: `4242 4242 4242 4242`
3. Verify countdown timer works
4. Test stealing a word after timer expires
5. Test message reporting
6. Access admin panel at `/admin/login`
7. Test content moderation

## Important Notes

- **Use test Stripe keys** for demo mode
- **Database initialization**: Run `init_db.py` and `migrate_add_moderation.py` on first deploy
- **Admin setup**: Enable `ADMIN_SETUP_ENABLED=True` temporarily to set up 2FA, then disable
- **Import words**: Optionally import 20k words using `import_words.py`

## Next Steps

1. ✅ Deployment configs created
2. [ ] Push to GitHub
3. [ ] Deploy to Railway
4. [ ] Deploy to Vercel
5. [ ] Test all functionality
6. [ ] Add Terms/Privacy pages (if required by Stripe)
7. [ ] Submit to Stripe for review

## Support Resources

- **Full Guide**: See `DEPLOYMENT.md` for detailed instructions
- **Railway Docs**: https://docs.railway.app
- **Vercel Docs**: https://vercel.com/docs
- **Stripe Testing**: https://stripe.com/docs/testing

## Cost Estimate (Free Tier)

- Vercel: Free (100GB bandwidth)
- Railway: $5 credit/month (~500 hours)
- Total: $0/month (if staying within free tier)

Good luck with deployment! 🚀
