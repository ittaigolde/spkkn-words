# The Word Registry - Development Braindump

**Last Updated:** 2026-01-27
**Status:** Phase P5 Complete - Production-Ready with Admin Panel, Deployment Infrastructure, and Backup/Restore

## Project Overview

The Word Registry is a gamified e-commerce platform where users purchase temporary "ownership" of English words. It operates on a "Steal & Shield" economy where ownership is never permanent - it's protected only for a duration proportional to the purchase price.

### Core Mechanics
- **Base Price:** All words start at $1.00
- **Price Escalator:** Each purchase increases the word's price by $1.00
- **Lockout Formula:** 1 hour of protection per $1.00 spent
- **Inventory:** 20,000 words imported (can scale to 480k later)
- **New Word Creation:** $50 flat fee (50 hours lockout)

## Current Implementation Status

### ✅ COMPLETED PHASES

#### Phase P0 - Backend Core (Complete)

#### Database Setup
- **PostgreSQL** database `word_registry` created and configured
- **Tables created:**
  - `words`: Stores all words with pricing, ownership, and lockout data
  - `transactions`: Immutable log of all purchases (with `is_admin_action` flag)
  - `error_logs`: Application error tracking
  - `word_views`: Analytics for word popularity
- **20,000 words imported** from `words-raw/20k.txt`
- All words initialized at $1.00 base price

#### FastAPI Backend Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # App entry point with router registration
│   ├── config.py         # Settings management (from .env)
│   ├── database.py       # SQLAlchemy engine & session management
│   ├── models.py         # Word, Transaction, ErrorLog, WordView models
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── services.py       # Business logic (steal_word, add_word, validation)
│   ├── utils.py          # Helper functions (is_word_available)
│   ├── cache.py          # Cache initialization & setup
│   ├── ratelimit.py      # Rate limiter setup (slowapi)
│   ├── rate_config.py    # Centralized rate limit configuration
│   ├── ml_models.py      # ML model loading (detoxify)
│   ├── admin_auth.py     # TOTP authentication for admin
│   ├── admin_service.py  # Admin business logic
│   └── routes/
│       ├── __init__.py
│       ├── words.py      # Word search/get/random endpoints
│       ├── purchase.py   # Purchase/add word endpoints
│       ├── leaderboard.py # Leaderboards & stats
│       ├── payment.py    # Stripe payment integration
│       └── admin.py      # Admin panel API endpoints
├── backups/              # Factory reset backups (git-ignored)
├── init_db.py            # Database schema initialization
├── import_words.py       # Word data import script
├── verify_import.py      # Quick DB verification script
├── create_database.py    # Alternative DB creation (if psql not available)
├── warmup_ml.py          # ML model warmup script
├── test_ratelimits.py    # Rate limit testing script
├── factory_reset.py      # Factory reset script (dangerous!)
├── restore_from_backup.py # Restore from backup script
├── migrate_admin_tables.py # Admin database migration
├── requirements.txt      # Python dependencies
├── .env                  # Environment config (DATABASE_URL, STRIPE_SECRET_KEY, etc.)
├── .env.example          # Template for .env
├── .gitignore            # Git ignore (includes backups/)
├── RATE_LIMIT_TESTING.md # Rate limit documentation
├── ADMIN_GUIDE.md        # Admin panel setup guide
├── ADMIN_PRODUCTION_SECURITY.md # Production security guide
├── FACTORY_RESET.md      # Factory reset & restore documentation
└── README.md
```

#### API Endpoints Implemented

**Words Management:**
- `GET /api/words/search` - Search words with filters (status, query, pagination)
- `GET /api/words/random` - Get random word (defaults to $1 available words)
- `GET /api/words/{word}` - Get word details + transaction history

**Purchase:**
- `POST /api/purchase/{word}` - Purchase a word
  - Request body: `{"owner_name": "string", "owner_message": "string"}`
  - Validates content (no URLs, profanity, emails, handles)
  - Checks availability (lockout expired or never owned)
  - Increases price by $1
  - Sets lockout (1 hour per $1 spent)
  - Creates transaction record
  - Uses row-level locking to prevent race conditions

**Leaderboards:**
- `GET /api/leaderboard/expensive` - Top N most expensive words
- `GET /api/leaderboard/recent` - Recent purchases
- `GET /api/leaderboard/stats` - Platform statistics (total words, revenue, etc.)

**Payment (Stripe):**
- `POST /api/payment/create-intent` - Create PaymentIntent for word purchase
- `POST /api/payment/confirm-purchase` - Confirm purchase after successful payment
- `POST /api/payment/webhook` - Handle Stripe webhook events

**Admin:**
- `POST /api/admin/login` - Verify TOTP code
- `GET /api/admin/setup` - Get QR code for initial setup (can be disabled)
- `GET /api/admin/dashboard` - Full dashboard data
- `GET /api/admin/income` - Income statistics
- `GET /api/admin/popular-words` - Most viewed words
- `GET /api/admin/errors` - Recent error logs
- `POST /api/admin/reset-word` - Reset word price/ownership (admin action)

**Health:**
- `GET /` - Basic health check
- `GET /health` - Detailed health check

#### Core Business Logic: `steal_word()`

Located in `app/services.py`, this is the heart of the purchase mechanic:

1. **Row-level locking** with `.with_for_update()` to prevent concurrent purchases
2. **Availability check** via `is_word_available()` helper
3. **Price calculation:** Current price becomes purchase price, new price = old + $1
4. **Lockout calculation:** `lockout_hours = purchase_price`, ends at `now + lockout_hours`
5. **Transaction record:** Immutable log entry created
6. **Atomic commit:** All changes happen in single DB transaction

#### Content Validation & Safety

`WordService.validate_content()` blocks:
- URLs and web links (http://, www., .com, etc.)
- Email addresses
- Social media handles (@username)
- Phone numbers
- Profanity (better-profanity library)
- Toxic/hateful content (detoxify ML model)

**Toxicity Detection:**
- `detoxify` library with transformers model (~400MB)
- Thresholds: 0.7 for words, 0.8 for messages
- Checks: toxicity, severe_toxicity, obscene, threat, insult, identity_attack
- Warmup script: `backend/warmup_ml.py`

#### Phase P1 - Frontend (Complete)

**Next.js 15.5.9 Setup:**
```
frontend/
├── app/
│   ├── layout.tsx         # Root layout with Header
│   ├── page.tsx           # Landing page
│   ├── word/
│   │   └── [word]/
│   │       └── page.tsx   # Dynamic word detail page
│   └── admin/
│       ├── login/
│       │   └── page.tsx   # Admin login (TOTP)
│       ├── setup/
│       │   └── page.tsx   # Admin setup (QR code)
│       └── dashboard/
│           └── page.tsx   # Admin dashboard
├── components/
│   ├── Header.tsx         # Navigation header
│   ├── CookieBanner.tsx   # GDPR/CCPA cookie consent
│   ├── PurchaseModal.tsx  # Demo purchase modal (pre-Stripe)
│   ├── PurchaseModalWithPayment.tsx  # Stripe payment modal
│   └── PaymentForm.tsx    # Stripe Elements payment form
├── lib/
│   ├── api.ts             # Centralized API client
│   └── adminApi.ts        # Admin API client with TOTP auth
└── package.json           # Dependencies
```

**Features Implemented:**
- ✅ Landing page with search functionality
- ✅ Random word button
- ✅ Leaderboards (expensive & recent words with messages)
- ✅ Word detail pages with live countdown timers
- ✅ Transaction history display
- ✅ Cookie consent banner
- ✅ Mandatory ownership acknowledgment checkbox
- ✅ Content validation on frontend (matches backend)
- ✅ Responsive design with Tailwind CSS
- ✅ Admin login page with TOTP code entry
- ✅ Admin setup page with QR code display
- ✅ Admin dashboard with income stats, popular words, errors, word reset

**Word Creation Feature ($50):**
- ✅ `POST /api/purchase/add/{word}` endpoint
- ✅ WordService.add_word() method
- ✅ Frontend UI to add new words not in registry
- ✅ Fixed price: $50 = 50 hours lockout
- ✅ Word validation: English only (ASCII), no emojis/foreign chars

#### Phase P2 - Stripe Integration (Complete)

**Backend Payment Routes:**
```
backend/app/routes/payment.py:
- POST /api/payment/create-intent     # Creates PaymentIntent
- POST /api/payment/confirm-purchase  # Confirms purchase after payment
- POST /api/payment/webhook           # Handles Stripe webhooks
```

**Frontend Payment Flow:**
1. User enters name and message
2. Acknowledges temporary ownership
3. Click "Continue to Payment"
4. Backend creates PaymentIntent
5. Stripe Payment Element loads with card form
6. User enters payment details
7. Stripe processes payment (supports 3D Secure)
8. Frontend confirms purchase with backend
9. Word ownership transferred

**Features:**
- ✅ Embedded payment form (no redirects)
- ✅ Test mode support on localhost
- ✅ Multiple payment methods (cards, Apple Pay, Google Pay)
- ✅ 3D Secure authentication built-in
- ✅ Webhook handling for payment notifications
- ✅ Graceful handling of payment_intent_unexpected_state errors
- ✅ Double-click prevention
- ✅ Comprehensive error handling
- ✅ Statement descriptor shows word purchased (e.g., "WORD* LOVE")

**Stripe Receipt Enhancement:**
- Credit card statement shows: `WORD* LOVE` (max 22 chars)
- Makes it clear which word was purchased
- Word truncated to 16 chars if needed for long words

**Test Cards:**
- Success: `4242 4242 4242 4242`
- 3D Secure: `4000 0025 0000 3155`
- Declined: `4000 0000 0000 0002`

**Documentation:** See `STRIPE_INTEGRATION.md` for complete setup guide

#### Phase P3 - Rate Limiting & Caching (Complete)

**Rate Limiting (slowapi):**
- Centralized configuration in `app/rate_config.py`
- Limits per endpoint:
  - Purchase word: 5/minute
  - Add word: 5/hour
  - Word search: 60/minute
  - Word detail: 100/minute
  - Random word: 100/minute
  - Leaderboard: 30/minute
  - Admin login: 10/minute
  - Default: 200/hour

**Caching (fastapi-cache2):**
- In-memory backend (Redis-ready for production)
- Cached endpoints:
  - Leaderboards (5 minute TTL)
  - Platform stats (5 minute TTL)
- Cache decorator: `@cache(expire=300)`

**Testing:**
- Test script: `backend/test_ratelimits.py`
- Color-coded output (green=pass, yellow=rate-limited, red=error)
- Handles business logic errors (400) vs rate limits (429)

#### Phase P4 - Admin Panel (Complete)

**Authentication:**
- TOTP (Time-based One-Time Password) with Google Authenticator
- 6-digit codes that refresh every 30 seconds
- No username/password - just TOTP codes
- X-Admin-Token header required for all admin requests
- Rate limiting: 10 login attempts per minute
- Session storage for tokens in browser

**Dashboard Features:**
- **Income Statistics:** Total, today, this week (excludes admin actions)
- **Popular Words:** Most viewed words in last 30 days (with view counts)
- **Error Logs:** Recent application errors with stack traces, endpoints, timestamps
- **Word Management:** Reset word price and ownership via modal

**Admin Actions:**
- Marked as `is_admin_action=true` in transactions
- Don't count towards revenue statistics
- Don't appear in public transaction history
- Used for moderation and corrections

**Analytics:**
- Word view tracking (powers popularity metrics)
- Error logging with stack traces, endpoints, IP addresses
- Income tracking separated from admin actions

**Database Tables:**
- `transactions.is_admin_action`: Boolean flag (default false)
- `error_logs`: Error tracking and monitoring
- `word_views`: Word page view analytics (with IP addresses)

**Frontend Pages:**
- `/admin/login`: TOTP code entry (6-digit numeric input)
- `/admin/setup`: QR code display for Google Authenticator
- `/admin/dashboard`: Comprehensive admin dashboard (auto-refresh every 30s)

**Production Security:**
- Setup page can be disabled with `ADMIN_SETUP_ENABLED=False` in .env
- Frontend shows friendly "Setup Disabled" message
- Backend returns 403 when disabled
- Multiple security approaches documented in `ADMIN_PRODUCTION_SECURITY.md`

**Setup:**
1. Generate TOTP secret: `python -c "import pyotp; print(pyotp.random_base32())"`
2. Add to `.env`: `ADMIN_TOTP_SECRET=your_secret_here`
3. Set `ADMIN_SETUP_ENABLED=True` for initial setup
4. Run migration: `python migrate_admin_tables.py`
5. Visit `/admin/setup` and scan QR code with Google Authenticator
6. Set `ADMIN_SETUP_ENABLED=False` for production
7. Access `/admin/login` with 6-digit code

**Documentation:**
- `ADMIN_GUIDE.md` - Complete setup guide
- `ADMIN_PRODUCTION_SECURITY.md` - Security best practices

#### Phase P5 - Deployment Infrastructure (Complete)

**DigitalOcean Deployment:**
- Ubuntu 22.04 setup scripts
- Nginx reverse proxy configuration
- Zero-downtime deployment support
- SSL/HTTPS with Let's Encrypt (Certbot)
- Systemd services for backend and frontend
- Automated health checks

**Deployment Scripts:**
- `setup-server.sh`: One-command server setup
- `deploy.sh`: Automated zero-downtime deployment
- `nginx.conf`: Production Nginx configuration
- Automated PostgreSQL backups

**Configuration:**
- Backend: Systemd service on port 8000
- Frontend: Systemd service on port 3000
- Nginx reverse proxy with rate limiting
- UFW firewall configuration (22, 80, 443)
- CORS properly configured for production

**Documentation:**
- `DEPLOYMENT.md` - Complete deployment guide
- `DEPLOYMENT_QUICK_REFERENCE.md` - Quick reference
- `PRE_DEPLOYMENT_CHECKLIST.md` - Pre-flight checklist

#### Phase P6 - Backup & Restore System (Complete)

**Factory Reset Script (`factory_reset.py`):**
- Two-factor confirmation: Type "RESET" then "ERASE"
- Automatic data export before any changes
- Deletes ALL words (including user-created)
- Deletes all transactions, error logs, word views
- Re-imports original 20,000 words from `words-raw/20k.txt`
- Shows before/after statistics
- Safe abort points (Ctrl+C before second confirmation)
- Color-coded terminal output

**Restore Script (`restore_from_backup.py`):**
- Lists all available backups with details
- Shows backup statistics (dates, counts, revenue)
- User selects which backup to restore
- Single confirmation: Type "RESTORE"
- Restores words by text match (maps old IDs to new IDs)
- Creates missing words from backup
- Updates existing words with backup data
- Restores transactions, error logs, word views
- Handles ID mapping automatically

**Backup Structure:**
```
backend/backups/
└── factory_reset_20260127_143022/
    ├── transactions.json      # All transaction history
    ├── word_states.json       # All word ownership states
    ├── error_logs.json        # All error logs
    ├── word_views.json        # All analytics data
    └── summary.json           # Statistics snapshot
```

**Key Features:**
- Backups stored in `backend/backups/` (git-ignored)
- Timestamped backup directories
- Complete data preservation before reset
- Automated word ID mapping during restore
- No data loss - everything backed up

**Usage:**
```bash
# Factory reset (dangerous!)
cd backend
python factory_reset.py

# Restore from backup
cd backend
python restore_from_backup.py
```

**Documentation:** `FACTORY_RESET.md` - Complete guide for both scripts

### 🔄 IN PROGRESS: None

### ❌ NOT YET IMPLEMENTED

#### Known Pending Items
- [ ] None - all planned features complete

#### Future Enhancements (Optional)
- [ ] UCP/Agentic layer (AI plugin manifest)
- [ ] Google Merchant Center feed generation
- [ ] Full 480k word dictionary import (currently 20k)
- [ ] Production Redis deployment (currently in-memory)
- [ ] WebSocket support for live updates
- [ ] Email notifications for outbid users
- [ ] Refund handling
- [ ] Dispute management

## Technical Details

### Environment Setup

**Python Version:** 3.13 (3.14 has compatibility issues with PyO3/Pydantic)

**Virtual Environment:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

**Backend Configuration:**
Edit `backend/.env`:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/word_registry
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=  # Optional for local testing
REDIS_URL=redis://localhost:6379  # Optional
RATE_LIMIT_ENABLED=True
CORS_ORIGINS=*  # Use specific domain in production
ADMIN_TOTP_SECRET=YOUR_SECRET_HERE
ADMIN_SETUP_ENABLED=True  # Set to False in production
```

**Frontend Configuration:**
Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

**Running the Backend:**
```bash
cd backend
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
uvicorn app.main:app --reload --port 8000
```

**Running the Frontend:**
```bash
cd frontend
npm run dev
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Admin Login: http://localhost:3000/admin/login
- Admin Setup: http://localhost:3000/admin/setup

### Database Schema

**words table:**
- `id` (PK, int)
- `text` (unique, indexed, varchar(100))
- `price` (numeric(10,2), default 1.00)
- `owner_name` (varchar(100), nullable)
- `owner_message` (varchar(140), nullable)
- `lockout_ends_at` (timestamp with timezone, nullable)
- `created_at` (timestamp with timezone)
- `updated_at` (timestamp with timezone)

**transactions table:**
- `id` (PK, int)
- `word_id` (FK → words.id)
- `buyer_name` (varchar(100))
- `price_paid` (numeric(10,2))
- `timestamp` (timestamp with timezone)
- `is_admin_action` (boolean, default false)

**error_logs table:**
- `id` (PK, int)
- `error_type` (varchar(100))
- `error_message` (text)
- `stack_trace` (text, nullable)
- `endpoint` (varchar(200), nullable)
- `user_info` (varchar(200), nullable)
- `timestamp` (timestamp with timezone)

**word_views table:**
- `id` (PK, int)
- `word_id` (FK → words.id)
- `timestamp` (timestamp with timezone)
- `ip_address` (varchar(45), nullable)

### Testing the API

**Example Test Sequence:**

1. Get platform stats:
```bash
GET http://localhost:8000/api/leaderboard/stats
```

2. Get a random $1 word:
```bash
GET http://localhost:8000/api/words/random
```

3. Create payment intent:
```bash
POST http://localhost:8000/api/payment/create-intent?word_text=hello&is_new_word=false
```

4. Complete payment with Stripe Elements (frontend)

5. Confirm purchase:
```bash
POST http://localhost:8000/api/payment/confirm-purchase
{
  "payment_intent_id": "pi_...",
  "word_text": "hello",
  "owner_name": "Alice",
  "owner_message": "My first word!",
  "is_new_word": false
}
```

6. Verify ownership:
```bash
GET http://localhost:8000/api/words/hello
# Should show: price=$2.00, locked, owner=Alice
```

7. Check leaderboards:
```bash
GET http://localhost:8000/api/leaderboard/expensive
GET http://localhost:8000/api/leaderboard/recent
```

8. Admin login:
```bash
POST http://localhost:8000/api/admin/login
{
  "totp_code": "123456"
}
```

## Key Design Decisions

1. **PostgreSQL over MySQL/SQLite:** Need ACID transactions and row-level locking for race condition prevention
2. **FastAPI over Flask/Django:** Better async support, automatic API docs, modern Python
3. **Pydantic for validation:** Type-safe request/response handling
4. **Separate services.py:** Business logic isolated from routes for testability
5. **Decimal for money:** Avoids floating-point precision issues
6. **Timezone-aware timestamps:** All datetime objects use UTC with timezone info
7. **TOTP over username/password:** More secure, no password storage/hashing needed
8. **Factory reset deletes all words:** Cleaner than tracking original vs user-created
9. **Backup/restore by text match:** Handles ID changes gracefully

## Known Issues / Production Notes

### Security
- ✅ CORS configured via environment variable (set specific domain in production)
- ✅ Admin setup page can be disabled in production
- ✅ TOTP authentication for admin access
- ✅ Rate limiting on all endpoints
- ✅ Content validation and toxicity detection
- ⚠️ Backups stored locally (git-ignored) - consider encrypted cloud storage

### Performance
- ⚠️ Rate limiting uses in-memory storage - deploy Redis for production clustering
- ⚠️ Caching uses in-memory backend - deploy Redis for production clustering
- ⚠️ detoxify model (~400MB) loads on first request - consider preloading on startup

### Monitoring
- ✅ Error logs stored in database
- ✅ Word view analytics
- ⚠️ No external monitoring service (consider Sentry/DataDog)

### Stripe
- ✅ Statement descriptor shows word purchased
- ✅ Test mode working on localhost
- ⚠️ Need to configure webhook endpoint for production
- ⚠️ Switch to live keys for production

## Production Deployment Checklist

### Pre-Deployment
- [ ] Set `CORS_ORIGINS` to specific domain in backend `.env`
- [ ] Set `ADMIN_SETUP_ENABLED=False` in backend `.env`
- [ ] Configure Stripe webhook endpoint
- [ ] Switch Stripe to live mode (live API keys)
- [ ] Deploy Redis for rate limiting & caching
- [ ] Set up SSL certificates (Let's Encrypt)
- [ ] Configure firewall (UFW)
- [ ] Set up automated database backups

### Deployment
- [ ] Deploy backend to DigitalOcean droplet (see `DEPLOYMENT.md`)
- [ ] Deploy frontend to Vercel or same droplet
- [ ] Configure Nginx reverse proxy
- [ ] Set up systemd services
- [ ] Test health endpoints
- [ ] Test payment flow with test cards
- [ ] Verify admin panel access
- [ ] Test factory reset in staging environment

### Post-Deployment
- [ ] Monitor error logs via admin panel
- [ ] Set up external monitoring (optional)
- [ ] Test email receipts from Stripe
- [ ] Verify webhook events are received
- [ ] Document production deployment details

## Quick Restart Checklist

If resuming this project:

**Backend:**
1. ✅ PostgreSQL installed and running
2. ✅ Database `word_registry` exists with all tables
3. ✅ Python 3.13 installed
4. ✅ Virtual environment at `backend/venv`
5. ✅ Dependencies installed via `requirements.txt`
6. ✅ `backend/.env` configured (DATABASE_URL, STRIPE keys, ADMIN_TOTP_SECRET)
7. ✅ 20,000 words imported
8. ✅ Admin tables migrated
9. Start backend: `cd backend && venv\Scripts\activate && uvicorn app.main:app --reload`

**Frontend:**
1. ✅ Node.js installed
2. ✅ Dependencies installed via `npm install`
3. ✅ `frontend/.env.local` configured (NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY)
4. Start frontend: `cd frontend && npm run dev`

**Admin:**
1. ✅ TOTP secret generated and in `.env`
2. ✅ Google Authenticator app configured
3. ✅ Admin setup page accessible (if `ADMIN_SETUP_ENABLED=True`)
4. Access: http://localhost:3000/admin/login

**Test:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Admin Login: http://localhost:3000/admin/login
- Test payment with card: `4242 4242 4242 4242`

## Reference Documents

- Full PRD: `prd.txt` (in project root)
- Word data: `words-raw/20k.txt` (20,000 words)
- API Docs: http://localhost:8000/docs (when server running)
- Stripe Setup: `STRIPE_INTEGRATION.md`
- Rate Limiting: `backend/RATE_LIMIT_TESTING.md`
- Admin Guide: `backend/ADMIN_GUIDE.md`
- Admin Security: `backend/ADMIN_PRODUCTION_SECURITY.md`
- Deployment: `backend/DEPLOYMENT.md`
- Backup/Restore: `backend/FACTORY_RESET.md`

---

## Git Commits

1. `a312cad` - Initial implementation of Phase P0: Core Backend API
2. `929ed3b` - Phase P1: Complete frontend + word creation + toxicity detection
3. `730816d` - Add frontend API client library
4. `1dc77c3` - Add rate limiting and caching (hybrid in-memory/Redis solution)
5. `d33d0a8` - Add Stripe Payment Element integration for secure payment processing
6. `efa5819` - Update BRAINDUMP.md to reflect completed phases P0-P2
7. `9e28ff3` - Add DigitalOcean droplet deployment infrastructure
8. `459df6a` - Add secure admin panel with TOTP authentication
9. `b1c0936` - Update ADMIN_GUIDE.md with complete setup instructions
10. `7b02fb0` - Add visual QR code setup page for admin TOTP
11. `6b20757` - Update ADMIN_GUIDE.md with setup page details
12. `5b2b2ab` - Add production security controls for admin setup page
13. `0304259` - Add factory reset script with two-factor confirmation and automatic backup
14. `17d4163` - Update factory reset to delete all words and re-import from 20k.txt
15. `1ab4439` - Add restore script and organize backups in dedicated directory
16. `fabad33` - Add word name to Stripe receipt and credit card statement

---

## Current State Summary

**Production-Ready Full-Stack Application:**
- ✅ Secure payment processing (Stripe) with word names in receipts
- ✅ Zero-downtime deployment infrastructure (Nginx + systemd)
- ✅ Admin panel with TOTP authentication
- ✅ Admin setup can be disabled for production security
- ✅ Analytics and error monitoring
- ✅ Factory reset with automatic backup
- ✅ Restore from backup capability
- ✅ Comprehensive documentation for all features
- ✅ Rate limiting and caching
- ✅ Content validation and toxicity detection
- ✅ Ready for production deployment to DigitalOcean

**Next Steps:** Deploy to production or extend with optional features (UCP/AI manifest, Google Merchant feed, expanded word inventory, etc.)

---

**Continuation Point:** All core features complete. Ready for production deployment or optional enhancements.
