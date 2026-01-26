# The Word Registry - Development Braindump

**Last Updated:** 2026-01-26
**Status:** Phase P2 Complete - Full-Stack Application with Stripe Payments

## Project Overview

The Word Registry is a gamified e-commerce platform where users purchase temporary "ownership" of English words. It operates on a "Steal & Shield" economy where ownership is never permanent - it's protected only for a duration proportional to the purchase price.

### Core Mechanics
- **Base Price:** All words start at $1.00
- **Price Escalator:** Each purchase increases the word's price by $1.00
- **Lockout Formula:** 1 hour of protection per $1.00 spent
- **Inventory:** 20,000 words imported (can scale to 480k later)

## Current Implementation Status

### ✅ COMPLETED PHASES

#### Phase P0 - Backend Core (Complete)

#### Database Setup
- **PostgreSQL** database `word_registry` created and configured
- **Tables created:**
  - `words`: Stores all words with pricing, ownership, and lockout data
  - `transactions`: Immutable log of all purchases
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
│   ├── models.py         # Word & Transaction models
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── services.py       # Business logic (steal_word, add_word, validation)
│   ├── utils.py          # Helper functions (is_word_available)
│   ├── cache.py          # Cache initialization & setup
│   ├── ratelimit.py      # Rate limiter setup (slowapi)
│   ├── rate_config.py    # Centralized rate limit configuration
│   ├── ml_models.py      # ML model loading (detoxify)
│   └── routes/
│       ├── __init__.py
│       ├── words.py      # Word search/get/random endpoints
│       ├── purchase.py   # Purchase/add word endpoints
│       ├── leaderboard.py # Leaderboards & stats
│       └── payment.py    # Stripe payment integration
├── init_db.py            # Database schema initialization
├── import_words.py       # Word data import script
├── verify_import.py      # Quick DB verification script
├── create_database.py    # Alternative DB creation (if psql not available)
├── warmup_ml.py          # ML model warmup script
├── test_ratelimits.py    # Rate limit testing script
├── requirements.txt      # Python dependencies
├── .env                  # Environment config (DATABASE_URL, STRIPE_SECRET_KEY, etc.)
├── .env.example          # Template for .env
├── RATE_LIMIT_TESTING.md # Rate limit documentation
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
│   └── word/
│       └── [word]/
│           └── page.tsx   # Dynamic word detail page
├── components/
│   ├── Header.tsx         # Navigation header
│   ├── CookieBanner.tsx   # GDPR/CCPA cookie consent
│   ├── PurchaseModal.tsx  # Demo purchase modal (pre-Stripe)
│   ├── PurchaseModalWithPayment.tsx  # Stripe payment modal
│   └── PaymentForm.tsx    # Stripe Elements payment form
├── lib/
│   └── api.ts             # Centralized API client
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

### 🔄 IN PROGRESS: None

### ❌ NOT YET IMPLEMENTED

#### Future Enhancements
- [ ] UCP/Agentic layer (AI plugin manifest)
- [ ] Google Merchant Center feed generation

#### Future Enhancements (Deferred)
- [ ] Full 480k word dictionary import (currently 20k)
- [ ] Production Redis deployment (currently in-memory)
- [ ] WebSocket support for live updates
- [ ] Admin dashboard for moderation
- [ ] Email notifications for outbid users
- [ ] Receipt emails (Stripe automatic receipts)
- [ ] Refund handling
- [ ] Dispute management
- [ ] Failed payment retry logic

## Technical Details

### Environment Setup

**Python Version:** 3.13 (3.14 has compatibility issues with PyO3/Pydantic)

**Virtual Environment:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
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
venv\Scripts\activate
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

3. Purchase the word "hello":
```bash
POST http://localhost:8000/api/purchase/hello
{
  "owner_name": "Alice",
  "owner_message": "My first word!"
}
```

4. Verify ownership:
```bash
GET http://localhost:8000/api/words/hello
# Should show: price=$2.00, locked, owner=Alice
```

5. Try to purchase again (should fail with lockout error):
```bash
POST http://localhost:8000/api/purchase/hello
{
  "owner_name": "Bob",
  "owner_message": "Trying to steal!"
}
# Returns 400: Word is currently locked
```

6. Check leaderboards:
```bash
GET http://localhost:8000/api/leaderboard/expensive
GET http://localhost:8000/api/leaderboard/recent
```

## Key Design Decisions

1. **PostgreSQL over MySQL/SQLite:** Need ACID transactions and row-level locking for race condition prevention
2. **FastAPI over Flask/Django:** Better async support, automatic API docs, modern Python
3. **Pydantic for validation:** Type-safe request/response handling
4. **Separate services.py:** Business logic isolated from routes for testability
5. **Decimal for money:** Avoids floating-point precision issues
6. **Timezone-aware timestamps:** All datetime objects use UTC with timezone info

## Known Issues / Notes

- CORS is currently wide open (`allow_origins=["*"]`) - tighten for production
- Rate limiting uses in-memory storage - deploy Redis for production clustering
- Caching uses in-memory backend - deploy Redis for production clustering
- detoxify model (~400MB) loads on first request - consider preloading on startup
- No email notifications for outbid users
- No admin interface for moderation
- Only 20k words imported (can scale to 480k)
- Test mode only for Stripe - need live keys for production

## Next Steps

1. **Production Deployment:**
   - Frontend: Deploy to Vercel
   - Backend: Deploy to Railway/Render/Fly.io
   - Database: Managed PostgreSQL (Railway/Render/Supabase)
   - Redis: Deploy for rate limiting & caching
   - Switch Stripe to live mode with live API keys

2. **Production Readiness:**
   - Tighten CORS to specific frontend domain
   - Configure Stripe webhook endpoint
   - Set up domain & SSL certificates
   - Configure environment variables in hosting platform

3. **Optional Enhancements:**
   - Import remaining 460k words
   - Build admin dashboard
   - Add email notifications
   - Implement UCP/AI plugin manifest
   - Google Merchant Center feed

## Reference Documents

- Full PRD: `prd.txt` (in project root)
- Word data: `words-raw/20k.txt` (20,000 words)
- API Docs: http://localhost:8000/docs (when server running)
- Stripe Setup: `STRIPE_INTEGRATION.md`
- Rate Limiting: `backend/RATE_LIMIT_TESTING.md`

## Quick Restart Checklist

If resuming this project:

**Backend:**
1. ✅ PostgreSQL installed and running
2. ✅ Database `word_registry` exists
3. ✅ Python 3.13 installed
4. ✅ Virtual environment at `backend/venv`
5. ✅ Dependencies installed via `requirements.txt`
6. ✅ `backend/.env` configured with DATABASE_URL and STRIPE_SECRET_KEY
7. ✅ 20,000 words imported
8. Start backend: `cd backend && venv\Scripts\activate && uvicorn app.main:app --reload`

**Frontend:**
1. ✅ Node.js installed
2. ✅ Dependencies installed via `npm install`
3. ✅ `frontend/.env.local` configured with NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
4. Start frontend: `cd frontend && npm run dev`

**Test:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Test payment with card: `4242 4242 4242 4242`

---

## Git Commits

1. `a312cad` - Initial implementation of Phase P0: Core Backend API
2. `929ed3b` - Phase P1: Complete frontend + word creation + toxicity detection
3. `730816d` - Add frontend API client library
4. `1dc77c3` - Add rate limiting and caching (hybrid in-memory/Redis solution)
5. `d33d0a8` - Add Stripe Payment Element integration for secure payment processing

---

**Continuation Point:** Full-stack application complete with Stripe payments working on localhost. Ready for production deployment or additional features.
