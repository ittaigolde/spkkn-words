# Caching and Rate Limiting

## Overview

The Word Registry implements a hybrid caching and rate limiting system that starts with in-memory solutions but can easily scale to Redis for production.

## Rate Limiting

**Library:** `slowapi` (Flask-Limiter for FastAPI)

### Rate Limits by Endpoint

| Endpoint | Limit | Reasoning |
|----------|-------|-----------|
| `POST /api/purchase/{word}` | 5/minute | Prevent spam purchases |
| `POST /api/purchase/add/{word}` | 2/hour | Prevent word spam creation |
| `GET /api/words/search` | 60/minute | Allow browsing, prevent scraping |
| `GET /api/words/{word}` | 100/minute | High read capacity |
| `GET /api/words/random` | 100/minute | High read capacity |
| `GET /api/leaderboard/*` | 30/minute | Cached, so less load |
| Global Default | 200/hour | Fallback for unlisted endpoints |

### Configuration

Rate limiting is enabled by default. To disable:

```env
RATE_LIMIT_ENABLED=False
```

### How It Works

- **Per-IP tracking:** Each IP address has its own counter
- **Sliding window:** Uses time-based windows (not fixed buckets)
- **Storage:** In-memory by default (can use Redis)
- **Error response:** HTTP 429 with retry information

### Upgrading to Redis

To use Redis for distributed rate limiting (multiple servers):

1. Install Redis: `docker run -d -p 6379:6379 redis`
2. Update `app/ratelimit.py`:
   ```python
   limiter = Limiter(
       key_func=get_remote_address,
       storage_uri="redis://localhost:6379",  # Change this line
   )
   ```

## Caching

**Library:** `fastapi-cache2`

### Cached Endpoints

| Endpoint | TTL | Description |
|----------|-----|-------------|
| `GET /api/leaderboard/expensive` | 30s | Most expensive words |
| `GET /api/leaderboard/recent` | 30s | Recent purchases |
| `GET /api/leaderboard/stats` | 60s | Platform statistics |

### Cache Backend

**Development:** In-memory cache (default)
- No dependencies
- Fast
- Cleared on server restart

**Production:** Redis cache (optional)
- Persistent across restarts
- Shared across multiple servers
- Better for horizontal scaling

### Upgrading to Redis

1. **Install Redis:**
   ```bash
   docker run -d -p 6379:6379 redis
   ```

2. **Set environment variable:**
   ```env
   REDIS_URL=redis://localhost:6379
   ```

3. **Restart server** - that's it! The code detects Redis and switches automatically.

### Cache Keys

Cache keys are automatically generated based on:
- Endpoint path
- Query parameters
- Request body (for POST requests)

Prefix: `word-registry:` (when using Redis)

### Manual Cache Invalidation

To invalidate cache manually (useful after purchases):

```python
from fastapi_cache import FastAPICache

# Clear all cache
await FastAPICache.clear()

# Clear specific key (Redis only)
await FastAPICache.clear(namespace="", key="specific_key")
```

## Monitoring

### Rate Limit Headers

Responses include rate limit headers:

```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 3
X-RateLimit-Reset: 1643723456
```

### Cache Headers

Responses include cache headers:

```
Cache-Control: public, max-age=30
X-FastAPI-Cache: Hit  # or Miss
```

## Performance Impact

### Before Caching/Rate Limiting
- Leaderboard query: ~50ms (DB aggregation)
- Stats query: ~100ms (multiple aggregations)
- Vulnerable to DDoS/abuse

### After (In-Memory)
- Leaderboard query: ~1ms (cache hit)
- Stats query: ~1ms (cache hit)
- Protected from basic abuse

### After (Redis)
- Leaderboard query: ~2-3ms (Redis + network)
- Stats query: ~2-3ms (Redis + network)
- Protected across multiple servers
- Survives restarts

## Testing

### Test Rate Limiting

```bash
# Should succeed 5 times, then fail
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/purchase/hello \
    -H "Content-Type: application/json" \
    -d '{"owner_name":"Test","owner_message":"Testing"}';
  echo "\n";
done
```

### Test Caching

```bash
# First request: Cache MISS
curl http://localhost:8000/api/leaderboard/stats -v

# Second request within 60s: Cache HIT
curl http://localhost:8000/api/leaderboard/stats -v
```

## Troubleshooting

### Rate Limit Persists After Restart

**In-memory:** Counters reset on restart (desired)
**Redis:** Counters persist (can manually clear)

### Cache Not Invalidating

Cache invalidates automatically after TTL. For immediate invalidation after purchases, you can add cache clearing in the purchase endpoints.

### Redis Connection Errors

Check Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

## Future Enhancements

- [ ] Add cache warming on startup
- [ ] Implement cache invalidation on word purchases
- [ ] Add per-user rate limiting (in addition to per-IP)
- [ ] Add admin endpoints to view/clear cache and rate limits
- [ ] Implement cache tagging for selective invalidation
