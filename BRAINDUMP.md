# The Word Registry - Development Braindump

**Last Updated:** 2026-01-26
**Status:** Phase P0 Complete - Core Backend API Functional

## Project Overview

The Word Registry is a gamified e-commerce platform where users purchase temporary "ownership" of English words. It operates on a "Steal & Shield" economy where ownership is never permanent - it's protected only for a duration proportional to the purchase price.

### Core Mechanics
- **Base Price:** All words start at $1.00
- **Price Escalator:** Each purchase increases the word's price by $1.00
- **Lockout Formula:** 1 hour of protection per $1.00 spent
- **Inventory:** 20,000 words imported (can scale to 480k later)

## Current Implementation Status

### ✅ COMPLETED: Phase P0 - Backend Core

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
│   ├── services.py       # Business logic (steal_word, validation)
│   ├── utils.py          # Helper functions (is_word_available)
│   └── routes/
│       ├── __init__.py
│       ├── words.py      # Word search/get/random endpoints
│       ├── purchase.py   # Purchase endpoint (steal_word)
│       └── leaderboard.py # Leaderboards & stats
├── init_db.py            # Database schema initialization
├── import_words.py       # Word data import script
├── verify_import.py      # Quick DB verification script
├── create_database.py    # Alternative DB creation (if psql not available)
├── requirements.txt      # Python dependencies
├── .env                  # Environment config (DATABASE_URL, etc.)
├── .env.example          # Template for .env
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

#### Content Validation

`WordService.validate_content()` blocks:
- URLs and web links (http://, www., .com, etc.)
- Email addresses
- Social media handles (@username)
- Phone numbers
- Basic profanity (extend list as needed)

### 🔄 IN PROGRESS: None (Phase P0 Complete)

### ❌ NOT YET IMPLEMENTED

#### Phase P1 (Next Priority - Frontend)
- [ ] Next.js frontend setup
- [ ] Landing page with search + random word generator
- [ ] Word detail page showing ownership, timer, history
- [ ] Checkout flow UI
- [ ] Cookie consent banner (GDPR/CCPA)
- [ ] Mandatory acknowledgment checkbox

#### Phase P2 (Medium Priority)
- [ ] Stripe payment integration
  - Checkout Sessions API
  - Dynamic statement descriptors (WR* WORD)
  - Webhook handling for payment confirmation
- [ ] UCP/Agentic layer (AI plugin manifest)
- [ ] Google Merchant Center feed generation

#### Future Enhancements
- [ ] Full 480k word dictionary import
- [ ] Advanced profanity filter (better-profanity library)
- [ ] Rate limiting & DDoS protection
- [ ] Caching layer (Redis) for leaderboards
- [ ] WebSocket support for live updates
- [ ] Admin dashboard

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

**Database Configuration:**
Edit `backend/.env`:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/word_registry
```

**Running the Server:**
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

API Docs: http://localhost:8000/docs

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

- Content validation is basic - consider using `better-profanity` library for production
- CORS is currently wide open (`allow_origins=["*"]`) - tighten for production
- No rate limiting yet - vulnerable to spam
- Stripe integration not implemented - purchase endpoint works without payment
- No email notifications for outbid users
- No admin interface for moderation

## Next Steps

1. **Set up Next.js frontend** in `/frontend` directory
2. **Build landing page** with:
   - Search bar
   - Random word button
   - Top 10 leaderboards (expensive & recent)
3. **Build word detail page** at `/word/[word]`:
   - Current ownership & message
   - Live countdown timer
   - Purchase button with price
   - Transaction history
4. **Integrate Stripe** for actual payments
5. **Deploy to production** (Vercel + Railway/Render)

## Reference Documents

- Full PRD: `prd.txt` (in project root)
- Word data: `words-raw/20k.txt` (20,000 words)
- API Docs: http://localhost:8000/docs (when server running)

## Quick Restart Checklist

If resuming this project:
1. ✅ PostgreSQL installed and running
2. ✅ Database `word_registry` exists
3. ✅ Python 3.13 installed
4. ✅ Virtual environment at `backend/venv`
5. ✅ Dependencies installed via `requirements.txt`
6. ✅ `.env` file configured with DATABASE_URL
7. ✅ 20,000 words imported
8. Start server: `uvicorn app.main:app --reload --port 8000`
9. Test at http://localhost:8000/docs

---

**Continuation Point:** Backend API is fully functional. Next session should focus on Phase P1 (Frontend).
