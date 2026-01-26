# Rate Limit Testing Guide

## Overview

This guide explains how to test and verify rate limiting is working correctly.

## Configuration

All rate limits are centralized in `app/rate_config.py`:

```python
class RateLimits:
    PURCHASE_WORD = "5/minute"     # Purchase existing word
    ADD_WORD = "2/hour"            # Add new word
    WORD_SEARCH = "60/minute"      # Search words
    WORD_DETAIL = "100/minute"     # Word detail page
    RANDOM_WORD = "100/minute"     # Random word endpoint
    LEADERBOARD = "30/minute"      # All leaderboard endpoints
    DEFAULT = "200/hour"           # Global fallback
```

## Adjusting Rate Limits

To change rate limits:

1. Open `backend/app/rate_config.py`
2. Modify the values (format: `"count/period"`)
3. Restart the server

**Valid periods:** `second`, `minute`, `hour`, `day`

**Examples:**
- `"10/second"` - 10 requests per second
- `"100/minute"` - 100 requests per minute
- `"5/hour"` - 5 requests per hour
- `"1/day"` - 1 request per day

## Testing Rate Limits

### Automated Test Script

Run the comprehensive test suite:

```bash
cd backend
venv\Scripts\activate
python test_ratelimits.py
```

**What it does:**
- Tests all endpoints with their configured rate limits
- Shows real-time results with color-coded output
- Verifies HTTP 429 (Rate Limit Exceeded) is returned
- Reports which endpoints are working correctly

**Output example:**
```
============================================================
Testing: Purchase Word (POST /api/purchase/{word})
Rate Limit: 5/minute (5 requests per minute)
============================================================
Request 1: Success (200)
Request 2: Success (200)
Request 3: Success (200)
Request 4: Success (200)
Request 5: Success (200)
Request 6: Rate limited (429) ✓

Summary:
  Successful requests: 5
  Rate limited: True
  ✓ Rate limit working correctly!
```

### Manual Testing

**Using cURL:**

```bash
# Test purchase endpoint (should fail after 5 requests)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/purchase/hello \
    -H "Content-Type: application/json" \
    -d '{"owner_name":"Test","owner_message":"Testing"}';
  echo "\n";
done
```

**Using browser/Postman:**

1. Open http://localhost:8000/docs
2. Try an endpoint repeatedly
3. After hitting the limit, you'll see:

```json
{
  "detail": "Rate limit exceeded: 5 per 1 minute",
  "retry_after": "Please try again later"
}
```

## Rate Limit Headers

Responses include these headers:

```
X-RateLimit-Limit: 5           # Max requests allowed
X-RateLimit-Remaining: 2       # Requests remaining
X-RateLimit-Reset: 1643723456  # Unix timestamp when limit resets
```

## Troubleshooting

### Rate Limit Not Working

**Check if enabled:**
```bash
# In .env file
RATE_LIMIT_ENABLED=True
```

**Verify server logs:**
Look for rate limit errors on startup.

### Rate Limit Too Strict

Edit `app/rate_config.py` and increase the limits:

```python
PURCHASE_WORD = "10/minute"  # Changed from 5/minute
```

### Rate Limit Too Loose

Decrease the limits or shorten the period:

```python
PURCHASE_WORD = "5/30second"  # 5 requests per 30 seconds
```

### Resetting Rate Limits

**In-memory (default):**
Restart the server - all counters reset

**Redis (if configured):**
```bash
redis-cli
FLUSHDB  # Clears all rate limit counters
```

## Production Recommendations

### Recommended Limits (High Traffic)

```python
class RateLimits:
    PURCHASE_WORD = "3/minute"      # Stricter to prevent abuse
    ADD_WORD = "1/hour"             # Very strict for new words
    WORD_SEARCH = "30/minute"       # Moderate for search
    WORD_DETAIL = "60/minute"       # Allow browsing
    RANDOM_WORD = "60/minute"       # Allow discovery
    LEADERBOARD = "20/minute"       # Cached, so can be lower
    DEFAULT = "100/hour"            # Tighter default
```

### DDoS Protection Layers

1. **Application (slowapi)** - Per-IP rate limiting ✓
2. **Reverse Proxy (nginx)** - Connection limits, request buffering
3. **CDN (Cloudflare)** - DDoS protection, WAF rules
4. **Infrastructure (AWS WAF)** - IP blocking, geo-blocking

### Monitoring

Watch these metrics in production:

- Rate limit hit rate (% of requests hitting 429)
- Top IPs by request count
- Endpoints with most rate limit violations
- Time to rate limit (how fast legitimate users hit limits)

## Advanced Configuration

### Different Limits for Authenticated Users

Modify `app/ratelimit.py` to use custom key functions:

```python
def get_user_identifier(request: Request) -> str:
    # Use API key or JWT token instead of IP
    api_key = request.headers.get("X-API-Key")
    return api_key if api_key else get_remote_address(request)

limiter = Limiter(key_func=get_user_identifier, ...)
```

### Whitelisting IPs

```python
def custom_key_func(request: Request) -> str:
    ip = get_remote_address(request)
    whitelist = ["127.0.0.1", "192.168.1.100"]
    return "" if ip in whitelist else ip  # Empty string = no limit

limiter = Limiter(key_func=custom_key_func, ...)
```

### Per-Endpoint Custom Responses

```python
@router.post("/critical-endpoint")
@limiter.limit("1/minute", error_message="This endpoint is heavily rate-limited. Please wait.")
async def critical_endpoint():
    pass
```
