# Admin Production Security Guide

This guide explains how to secure the admin setup endpoint in production.

## Why Disable the Setup Page?

The `/admin/setup` endpoint exposes your TOTP secret via a QR code. While this is convenient for initial setup, **it should never be accessible in production** as it would allow anyone to generate valid admin codes.

## Option 1: Environment Variable (Recommended) ✅

**Easiest and most flexible approach.**

### Setup

1. **In Development** (leave enabled):
   ```env
   # backend/.env
   ADMIN_SETUP_ENABLED=True
   ```

2. **In Production** (disable after setup):
   ```env
   # backend/.env (production)
   ADMIN_SETUP_ENABLED=False
   ```

### How It Works

- When `ADMIN_SETUP_ENABLED=False`, both endpoints return 403:
  - `/api/admin/setup` (backend API)
  - `/admin/setup` (frontend page)

- The frontend shows a friendly "Setup Disabled" message with instructions

### Advantages

✅ No code changes needed
✅ Easy to re-enable if needed (just change .env)
✅ Works across all environments
✅ Graceful error handling

### To Re-Enable

If you need to set up a new device:

1. Set `ADMIN_SETUP_ENABLED=True` in `.env`
2. Restart backend server
3. Visit `/admin/setup`
4. Scan QR code
5. Set `ADMIN_SETUP_ENABLED=False` again
6. Restart backend server

## Option 2: Remove Routes (Most Secure) 🔒

**Permanent removal from production code.**

### How to Implement

Comment out or delete the setup route in `backend/app/routes/admin.py`:

```python
# @router.get("/setup")
# @limiter.limit("5/minute")
# async def admin_setup(request: Request):
#     """DISABLED IN PRODUCTION"""
#     raise HTTPException(status_code=404, detail="Not found")
```

And remove/rename the frontend page:
```bash
# Rename to prevent access
mv frontend/app/admin/setup frontend/app/admin/_setup_disabled
```

### Advantages

✅ Most secure (route doesn't exist)
✅ No accidental re-enable
✅ Smaller attack surface

### Disadvantages

❌ Requires code changes
❌ Harder to re-enable (need to uncomment/restore)
❌ Different code between dev and production

## Option 3: IP Whitelist

**Allow only specific IP addresses.**

### How to Implement

Add IP check to the setup endpoint:

```python
from fastapi import Request

ALLOWED_IPS = ["127.0.0.1", "YOUR_OFFICE_IP"]

@router.get("/setup")
@limiter.limit("5/minute")
async def admin_setup(request: Request):
    client_ip = request.client.host if request.client else None

    if client_ip not in ALLOWED_IPS:
        raise HTTPException(status_code=403, detail="Access denied")

    # ... rest of setup code
```

### Advantages

✅ Accessible from specific locations
✅ No need to disable/enable
✅ Good for office environments

### Disadvantages

❌ Requires knowing your IP
❌ Doesn't work with dynamic IPs
❌ Extra code complexity

## Option 4: Setup Token

**Require a separate secret token.**

### How to Implement

1. Add to `.env`:
   ```env
   ADMIN_SETUP_TOKEN=your_random_token_here
   ```

2. Modify endpoint:
   ```python
   @router.get("/setup")
   async def admin_setup(
       request: Request,
       token: str = Query(None, description="Setup token")
   ):
       if token != settings.admin_setup_token:
           raise HTTPException(status_code=403, detail="Invalid setup token")

       # ... rest of setup code
   ```

3. Access with token:
   ```
   http://localhost:8000/api/admin/setup?token=your_random_token_here
   ```

### Advantages

✅ Can be shared securely
✅ Easy to rotate
✅ Works from any location

### Disadvantages

❌ Token could be leaked
❌ Extra complexity
❌ Need to manage two secrets

## Comparison Table

| Method | Security | Ease of Use | Re-Enable | Best For |
|--------|----------|-------------|-----------|----------|
| **Environment Variable** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Easy | **Most Users** |
| **Remove Routes** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Hard | High Security |
| **IP Whitelist** | ⭐⭐⭐ | ⭐⭐⭐ | N/A | Fixed Location |
| **Setup Token** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | N/A | Shared Access |

## Recommended Approach

**For most users: Use Option 1 (Environment Variable)**

### Initial Setup (Development)

```env
# backend/.env
ADMIN_SETUP_ENABLED=True
ADMIN_TOTP_SECRET=JBSWY3DPEHPK3PXP
```

1. Visit `/admin/setup`
2. Scan QR code with Google Authenticator
3. Save secret in password manager
4. Test login at `/admin/login`

### Production Deployment

```env
# backend/.env (production)
ADMIN_SETUP_ENABLED=False
ADMIN_TOTP_SECRET=JBSWY3DPEHPK3PXP
```

1. Set `ADMIN_SETUP_ENABLED=False`
2. Deploy to production
3. Setup endpoint returns 403
4. Admin login still works normally

### If You Need to Re-Setup

```env
# Temporarily enable
ADMIN_SETUP_ENABLED=True
```

1. Enable setup endpoint
2. Restart backend
3. Access `/admin/setup`
4. Scan with new device
5. Disable again: `ADMIN_SETUP_ENABLED=False`
6. Restart backend

## Nginx Protection (Additional Security)

If using Nginx, you can also block the endpoint:

```nginx
# In your nginx.conf
location /api/admin/setup {
    deny all;
    return 403;
}

location /admin/setup {
    deny all;
    return 403;
}
```

This adds an extra layer even if the environment variable is misconfigured.

## Verification Checklist

Before going to production:

- [ ] `ADMIN_SETUP_ENABLED=False` in production `.env`
- [ ] TOTP secret saved in password manager
- [ ] Successfully logged in with Google Authenticator
- [ ] Tested that `/admin/setup` returns 403 or friendly error
- [ ] Backend restarted with production configuration
- [ ] Admin dashboard accessible with TOTP code
- [ ] (Optional) Nginx rules added
- [ ] (Optional) Security audit completed

## Emergency Recovery

**Lost access to Google Authenticator?**

1. SSH into your server
2. Generate new TOTP secret:
   ```bash
   python -c "import pyotp; print(pyotp.random_base32())"
   ```
3. Update `ADMIN_TOTP_SECRET` in `.env`
4. Enable setup: `ADMIN_SETUP_ENABLED=True`
5. Restart backend
6. Visit `/admin/setup` and scan new QR code
7. Disable setup: `ADMIN_SETUP_ENABLED=False`
8. Restart backend

## Security Best Practices

1. ✅ **Always disable setup in production**
2. ✅ **Use HTTPS** (required for secure TOTP transmission)
3. ✅ **Save TOTP secret** in password manager as backup
4. ✅ **Monitor admin access** via error logs
5. ✅ **Rotate secrets** periodically (every 6-12 months)
6. ✅ **Limit admin access** to trusted networks if possible
7. ✅ **Enable rate limiting** (already configured)
8. ✅ **Use strong secrets** (32+ characters, base32 encoded)

## Monitoring

Check if setup endpoint is accessible:

```bash
# Should return 403 in production
curl -I https://yourdomain.com/api/admin/setup

# Should return 403 or redirect
curl -I https://yourdomain.com/admin/setup
```

Add monitoring alerts for:
- Multiple failed admin login attempts
- Setup endpoint accessed in production
- TOTP secret changes

## Questions?

**Q: Can I have multiple admins with different codes?**
A: Not currently. You'd need to extend the system to support multiple TOTP secrets. For now, share the same secret across trusted devices.

**Q: What if someone gets my TOTP secret?**
A: Immediately generate a new secret, update `.env`, restart, and re-scan QR code on all devices.

**Q: Do I need to keep the setup page enabled?**
A: No. Once you've scanned the QR code, you can disable it permanently.

**Q: Can I use Authy instead of Google Authenticator?**
A: Yes! Any TOTP-compatible app works (Authy, Microsoft Authenticator, 1Password, etc.)

**Q: How do I know if setup is disabled?**
A: Visit `/admin/setup` - you'll see a "Setup Disabled" message with a lock icon.

---

**Remember:** The setup endpoint exists to make initial configuration easy. Once you've scanned the QR code, disable it for security!
