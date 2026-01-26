# The Word Registry - Frontend

Next.js frontend for The Word Registry platform.

## Features

- **Landing Page:** Search bar, random word generator, and top 10 leaderboards
- **Word Detail Pages:** Dynamic pages with live countdown timers, ownership info, and transaction history
- **Purchase Flow:** Modal-based checkout with content validation and mandatory acknowledgment
- **Cookie Consent:** GDPR/CCPA compliant cookie banner
- **Responsive Design:** Mobile-friendly Tailwind CSS styling

## Setup

### Prerequisites
- Node.js 18+ and npm
- Backend API running on http://localhost:8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open http://localhost:3000 in your browser

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout with header/footer
│   ├── page.tsx            # Landing page
│   ├── globals.css         # Global styles
│   └── word/
│       └── [word]/
│           └── page.tsx    # Dynamic word detail page
├── components/
│   ├── PurchaseModal.tsx   # Purchase flow modal
│   └── CookieBanner.tsx    # GDPR cookie consent
├── lib/
│   └── api.ts              # API client and types
└── package.json
```

## API Integration

The frontend connects to the backend API via `/api/*` routes, which are proxied to `http://localhost:8000/api/*` in `next.config.ts`.

## Building for Production

```bash
npm run build
npm start
```

## Next Steps

- [ ] Integrate Stripe payment processing
- [ ] Add success/confetti animation on purchase
- [ ] Implement search results page
- [ ] Add loading skeletons
- [ ] SEO optimization for word pages
- [ ] Add social sharing functionality
