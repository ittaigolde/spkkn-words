# Stripe Payment Integration Guide

## Overview

The Word Registry uses **Stripe Payment Element** (Option B) for embedded payment processing. Payments are processed directly on your site with Stripe handling all PCI compliance.

## Features

✅ **Embedded payment form** - No redirects, stays on your site
✅ **Test mode support** - Full testing on localhost
✅ **Multiple payment methods** - Cards, Apple Pay, Google Pay (automatic)
✅ **3D Secure support** - Built-in authentication
✅ **Webhook handling** - Real-time payment notifications

## Setup Instructions

### 1. Create Stripe Account

1. Sign up at https://stripe.com (free)
2. Verify your email
3. You'll be in **Test Mode** by default (perfect for localhost)

### 2. Get API Keys

1. Go to https://dashboard.stripe.com/test/apikeys
2. Copy your **Publishable key** (starts with `pk_test_...`)
3. Copy your **Secret key** (starts with `sk_test_...`)
4. Keep these safe!

### 3. Configure Backend

**Create/edit `backend/.env`:**
```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
STRIPE_WEBHOOK_SECRET=  # Leave empty for now
```

### 4. Configure Frontend

**Create `frontend/.env.local`:**
```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Stripe Configuration
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
```

### 5. Install Dependencies

**Backend:**
```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt  # stripe already included
```

**Frontend:**
```bash
cd frontend
npm install  # Installs @stripe/stripe-js and @stripe/react-stripe-js
```

### 6. Start Servers

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Testing Payments

### Test Cards

Use these test card numbers (they work on localhost!):

| Card Number | Result |
|-------------|--------|
| `4242 4242 4242 4242` | ✅ Success |
| `4000 0025 0000 3155` | ✅ 3D Secure required |
| `4000 0000 0000 9995` | ❌ Insufficient funds |
| `4000 0000 0000 0002` | ❌ Card declined |
| `4000 0000 0000 9987` | ❌ Lost card |

**Card details for testing:**
- Expiry: Any future date (e.g., `12/25`)
- CVC: Any 3 digits (e.g., `123`)
- ZIP: Any 5 digits (e.g., `12345`)

### Testing Flow

1. Open http://localhost:3000
2. Click on a word or add a new word
3. Enter your name and message
4. Acknowledge the terms
5. Click "Continue to Payment"
6. Enter test card: `4242 4242 4242 4242`
7. Complete payment
8. Word ownership updated instantly!

## Payment Flow

### User Journey:

1. **Step 1: Details**
   - User enters name and message
   - Acknowledges temporary ownership
   - Clicks "Continue to Payment"

2. **Step 2: Payment Intent Created**
   - Backend: `POST /api/payment/create-intent`
   - Stripe creates PaymentIntent
   - Returns `client_secret`

3. **Step 3: Payment Form**
   - Frontend shows Stripe Payment Element
   - User enters card details
   - Stripe handles validation and 3D Secure

4. **Step 4: Confirmation**
   - Frontend: `stripe.confirmPayment()`
   - Backend: `POST /api/payment/confirm-purchase`
   - Word ownership transferred
   - Success!

## Webhook Setup (Optional for Production)

Webhooks allow Stripe to notify your backend when payments succeed/fail.

### Local Testing with Stripe CLI

1. **Install Stripe CLI:**
   - Download from: https://stripe.com/docs/stripe-cli
   - Or use: `winget install stripe`

2. **Login:**
   ```bash
   stripe login
   ```

3. **Forward webhooks to localhost:**
   ```bash
   stripe listen --forward-to localhost:8000/api/payment/webhook
   ```

4. **Get webhook signing secret:**
   - CLI will show: `whsec_...`
   - Add to `backend/.env`:
     ```env
     STRIPE_WEBHOOK_SECRET=whsec_your_secret_here
     ```

5. **Test a payment** - webhook events will be forwarded!

### Production Webhooks

1. Go to https://dashboard.stripe.com/webhooks
2. Add endpoint: `https://yoursite.com/api/payment/webhook`
3. Select events: `payment_intent.succeeded`, `payment_intent.payment_failed`
4. Copy webhook signing secret to your production `.env`

## API Endpoints

### POST /api/payment/create-intent

Creates a PaymentIntent for a word purchase.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/payment/create-intent?word_text=hello&is_new_word=false"
```

**Response:**
```json
{
  "client_secret": "pi_xxx_secret_xxx",
  "amount": 100,
  "word": "hello",
  "is_new_word": false
}
```

### POST /api/payment/confirm-purchase

Confirms purchase after successful payment.

**Request:**
```json
{
  "payment_intent_id": "pi_xxx",
  "word_text": "hello",
  "owner_name": "Alice",
  "owner_message": "Hello world!",
  "is_new_word": false
}
```

**Response:**
```json
{
  "success": true,
  "word": "hello",
  "transaction_id": 123,
  "message": "Purchase completed successfully!"
}
```

### POST /api/payment/webhook

Receives Stripe webhook events.

**Headers:**
- `stripe-signature`: Webhook signature

**Events handled:**
- `payment_intent.succeeded`
- `payment_intent.payment_failed`

## Troubleshooting

### "No such token" error

- Your publishable key is invalid or not set
- Check `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` in `frontend/.env.local`

### "Payment intent not found"

- Your secret key is invalid or not set
- Check `STRIPE_SECRET_KEY` in `backend/.env`

### Payment form not showing

- Check browser console for errors
- Verify frontend has Stripe packages installed: `npm list @stripe/stripe-js`
- Verify publishable key starts with `pk_test_`

### Webhook signature verification failed

- Remove or leave empty `STRIPE_WEBHOOK_SECRET` for local testing
- For production, ensure webhook secret matches Stripe dashboard

### CORS errors

- Backend CORS is configured for `*` (all origins)
- If issues persist, check `backend/app/main.py` CORS middleware

## Going Live

### Before Production:

1. **Switch to Live Mode** in Stripe Dashboard
2. Get **live API keys** (start with `pk_live_` and `sk_live_`)
3. Update environment variables with live keys
4. **Enable webhooks** with production URL
5. **Test thoroughly** with real cards
6. Consider adding:
   - Receipt emails (Stripe automatic receipts)
   - Refund handling
   - Dispute management
   - Failed payment retry logic

### Security Checklist:

- ✅ Never expose secret key to frontend
- ✅ Always verify webhook signatures
- ✅ Use HTTPS in production
- ✅ Validate all user inputs
- ✅ Log payment events
- ✅ Monitor failed payments

## Monitoring

### Stripe Dashboard

View real-time payments at: https://dashboard.stripe.com/test/payments

**Useful views:**
- Payments - See all transactions
- Logs - Debug API requests
- Webhooks - View webhook deliveries
- Events - See all Stripe events

### Backend Logs

Payment events are logged:
```
Payment succeeded: pi_xxx
Payment failed: pi_yyy
```

## Cost

### Test Mode (Development)
- **Free** - Unlimited test transactions
- No real money involved
- Perfect for localhost testing

### Live Mode (Production)
- **2.9% + $0.30** per successful card transaction (US)
- No monthly fees
- No setup fees
- Only pay when you get paid

## Support

- Stripe Docs: https://stripe.com/docs
- Test Cards: https://stripe.com/docs/testing
- Stripe CLI: https://stripe.com/docs/stripe-cli
- Discord/Support: https://support.stripe.com
