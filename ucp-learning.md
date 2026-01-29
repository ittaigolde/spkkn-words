# UCP.dev Integration Learning Journey

Documentation of integrating spkkn.com (The Word Registry) with Google Merchant Center and ucp.dev for agentic checkout.

---

## Goal
Enable AI agents to discover and purchase words from our inventory via ucp.dev's agentic checkout system.

---

## Phase 1: Google Merchant Center Setup

### What is Google Merchant Center?
- Google's platform for merchants to upload product data
- Makes products discoverable across Google services (Shopping, Search, etc.)
- Required for ucp.dev integration (AI agents discover products here)

### Prerequisites
- ✅ Live website: https://spkkn.com
- ✅ Payment processing: Stripe (live mode)
- ✅ Product inventory: 20,000 words
- ✅ SSL certificate enabled
- ⏳ Google Account
- ⏳ Business information

### Step 1: Create Google Merchant Center Account

**Instructions:**
1. Go to https://merchants.google.com
2. Sign in with Google account (or create one)
3. Click "Get Started" or "Create Account"
4. Choose account type:
   - **Business name**: The Word Registry (or your business name)
   - **Country**: United States (or your country)
   - **Time zone**: Your local timezone
5. Accept Terms of Service

**What you'll need:**
- Business email address
- Business website URL: https://spkkn.com
- Customer service email/phone
- Return/refund policy (even if it's "all sales final")

### Step 2: Verify and Claim Your Website

Google needs to verify you own spkkn.com. Methods available:
1. **HTML tag** - Add meta tag to website header
2. **HTML file upload** - Upload verification file to website
3. **Google Analytics** - If you already use it
4. **Google Tag Manager** - If you already use it
5. **Domain name provider** - Add DNS record

**Recommended: HTML tag method**
- Easiest for Next.js sites
- Add to `frontend/app/layout.tsx` in the `<head>` section

### Step 3: Configure Business Information

Required information:
- **Business name**: The Word Registry
- **Business address**: (if applicable)
- **Customer service contact**: Email/phone for customer inquiries
- **Website URL**: https://spkkn.com

### Step 4: Set Up Shipping & Tax

For digital products (our words):
- **Shipping**: Not applicable (digital delivery, instant)
- **Tax**: May need to configure based on your location
- US sellers: May need to collect sales tax depending on state

### Step 5: Create Product Feed

Product feed = structured data file containing all your products (words).

**Feed format options:**
- Google Sheets
- XML file
- JSON file (via Content API)
- CSV file

**Required fields for each product:**
- `id` - Unique product identifier (e.g., word ID)
- `title` - Product name (e.g., "Word: LOVE")
- `description` - Product description
- `link` - URL to product page (e.g., https://spkkn.com/word/love)
- `image_link` - Product image URL (we may need to generate images)
- `price` - Current price (e.g., "1.00 USD")
- `availability` - in_stock / out_of_stock / preorder
- `condition` - new / used / refurbished (use "new" for digital)
- `brand` - Your brand name (e.g., "The Word Registry")

**Our specific considerations:**
- 20,000 products (words) to list
- Prices change dynamically as words are purchased
- Availability changes (locked vs available)
- Need to generate product images (word cards?)

---

## Phase 2: UCP.dev Integration (Coming Next)

After Google Merchant Center setup is complete, we'll integrate with ucp.dev to enable AI agent checkout.

---

## Resources
- Google Merchant Center: https://merchants.google.com
- Google Merchant Center Help: https://support.google.com/merchants
- UCP.dev: https://ucp.dev
- Product Feed Specifications: https://support.google.com/merchants/answer/7052112

---

## Notes & Learnings

**2026-01-29:**
- Started documentation
- Identified that digital products need different shipping/tax handling
- Need to decide on product feed format (likely JSON via API for dynamic pricing)
- May need to generate product images for each word


---

**2026-01-29 - Product Feed API Created:**

Built product feed infrastructure with two endpoints:

**1. JSON Feed Endpoint:**
- URL: `https://spkkn.com/api/product-feed/google-merchant`
- Format: JSON (Google Merchant Center Content API compatible)
- Returns all 20,000 words with:
  - Unique ID
  - Title: "Word: {WORD}"
  - Description with ownership info
  - Link to product page
  - Image link (placeholder for now)
  - Current price in USD
  - Availability (in_stock/out_of_stock based on lockout)
  - Condition: new
  - Brand: The Word Registry
  - Custom labels for filtering (available/locked, owned/unclaimed, price tier)

**2. XML/RSS Feed Endpoint:**
- URL: `https://spkkn.com/api/product-feed/google-merchant/rss`
- Format: RSS/XML
- Alternative format for XML-based feeds
- Same data as JSON endpoint

**3. Word Image Endpoint:**
- URL: `https://spkkn.com/api/product-feed/word-image/{word}`
- Currently redirects to placeholder
- TODO: Generate actual word card images dynamically

**Key Features:**
- Dynamic pricing: Feed shows current price for each word
- Dynamic availability: Automatically marks locked words as out_of_stock
- Owner information: Shows if word is owned or unclaimed
- Filtering labels: Price tiers, availability status, ownership status
- Testing support: `?limit=N` parameter to test with subset of products

**Next Steps:**
1. Deploy and test the feed endpoints
2. Verify feed in Google Merchant Center
3. (Optional) Generate custom word card images
4. Set up automatic feed updates/refresh

