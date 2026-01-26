# Admin System Guide

The Word Registry includes a secure admin panel protected by TOTP (Time-based One-Time Password) authentication using Google Authenticator.

## Features

### Dashboard
- **Income Statistics**
  - Total all-time income
  - Today's income
  - This week's income
  - Transaction counts (excludes admin actions)

- **Popular Words**
  - Most viewed words in the last 30 days
  - View counts, prices, and current owners

- **Error Logs**
  - Recent application errors
  - Stack traces and endpoint information
  - User information (IP addresses)

- **Word Management**
  - Reset word price
  - Set word ownership
  - Admin actions don't count in revenue stats

## Security

### TOTP Authentication
- Uses Google Authenticator or compatible TOTP apps
- 6-digit codes that refresh every 30 seconds
- No username/password - just TOTP codes
- Token required in X-Admin-Token header for all admin API requests

### Rate Limiting
- Admin login: 10 attempts per minute
- Setup endpoint: 5 requests per minute

### Admin Actions Tracking
- All admin word resets are marked as `is_admin_action=true`
- These transactions don't count towards revenue statistics
- Clearly separated from real purchases

## Setup Instructions

### 1. Generate TOTP Secret

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -c "import pyotp; print(pyotp.random_base32())"
```

This will output something like: `JBSWY3DPEHPK3PXP`

### 2. Add to Environment

Add the secret to `backend/.env`:

```env
ADMIN_TOTP_SECRET=JBSWY3DPEHPK3PXP
```

**IMPORTANT:** Keep this secret secure! Anyone with this secret can generate valid admin codes.

### 3. Install Dependencies

```bash
cd backend
pip install pyotp qrcode pillow
```

Or reinstall from requirements:

```bash
pip install -r requirements.txt
```

### 4. Run Database Migration

```bash
cd backend
python migrate_admin_tables.py
```

This adds:
- `is_admin_action` column to `transactions` table
- `error_logs` table
- `word_views` table

### 5. Get QR Code

Start your backend server, then visit:

```
http://localhost:8000/api/admin/setup
```

This will return JSON with a base64-encoded QR code image:

```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,...",
  "manual_entry": "JBSWY3DPEHPK3PXP",
  "instructions": "..."
}
```

**Option A:** Display the QR code:
- Copy the `qr_code` value
- Paste it as `src` in an `<img>` tag in your browser
- Scan with Google Authenticator

**Option B:** Manual entry:
- Open Google Authenticator
- Choose "Enter a setup key"
- Account name: "Word Registry Admin"
- Your key: (paste the secret)
- Type of key: Time based

### 6. Disable Setup Endpoint (Production)

**IMPORTANT:** In production, you should disable or protect the `/api/admin/setup` endpoint since it exposes your TOTP secret.

Options:
1. Remove the route after initial setup
2. Add IP whitelist
3. Require a separate setup token

## Usage

### Access Admin Panel

1. Navigate to: `https://yourdomain.com/admin/login`
2. Open Google Authenticator on your phone
3. Enter the 6-digit code shown for "Word Registry Admin"
4. Click "Sign In"

Codes refresh every 30 seconds, so enter them promptly!

### Dashboard Features

**Income Stats:**
- View total revenue (excluding admin actions)
- Track today's and this week's income
- See transaction counts

**Popular Words:**
- See which words are getting the most views
- Sort by view count
- Shows last 30 days of data

**Error Logs:**
- Monitor application errors
- See stack traces for debugging
- Track endpoints where errors occur

**Reset Word:**
1. Click "Reset Word" button
2. Enter word text (e.g., "hello")
3. Set new price (e.g., "1.00")
4. Optionally set owner name and message
5. Click "Reset Word"

**Note:** Reset actions are marked as admin actions and don't count towards revenue statistics.

### Logout

Click "Logout" button in the header. This clears your stored token.

## API Endpoints

All admin endpoints require `X-Admin-Token` header with a valid 6-digit TOTP code.

### POST /api/admin/login
Verify TOTP code.

**Request:**
```json
{
  "totp_code": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Authentication successful"
}
```

### GET /api/admin/dashboard
Get complete dashboard data.

**Headers:**
```
X-Admin-Token: 123456
```

**Response:**
```json
{
  "income": {
    "total_income": 1234.56,
    "today_income": 50.00,
    "week_income": 300.00,
    "total_transactions": 500,
    "today_transactions": 10,
    "week_transactions": 75
  },
  "popular_words": [...],
  "recent_errors": [...],
  "stats": {
    "total_words": 20000,
    "available_words": 19500,
    "locked_words": 500
  }
}
```

### GET /api/admin/income
Get income statistics only.

### GET /api/admin/popular-words?limit=20
Get most viewed words.

### GET /api/admin/errors?limit=50
Get recent error logs.

### POST /api/admin/reset-word
Reset a word's price and ownership.

**Request:**
```json
{
  "word": "hello",
  "new_price": 1.00,
  "owner_name": "Admin",
  "owner_message": "Reset by admin"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Word 'hello' has been reset",
  "word": {
    "text": "hello",
    "price": 1.00,
    "owner_name": "Admin",
    "owner_message": "Reset by admin",
    "lockout_ends_at": "2026-01-27T12:00:00Z"
  }
}
```

## Error Logging

### Automatic Error Logging

The system automatically logs errors to the `error_logs` table. To integrate error logging throughout your application:

```python
from app.admin_service import AdminService

try:
    # Your code here
    pass
except Exception as e:
    AdminService.log_error(
        db=db,
        error_type="YourErrorType",
        error_message=str(e),
        stack_trace=traceback.format_exc(),
        endpoint="/api/your-endpoint",
        user_info=request.client.host if request.client else None
    )
    raise
```

### View Logging

Word views are automatically tracked when users visit word detail pages. This powers the "Most Viewed Words" feature.

## Troubleshooting

### "Invalid or expired admin token"

- TOTP codes are only valid for 60 seconds (30 second window on each side)
- Make sure your device time is synchronized
- Try waiting for the next code to appear
- Check that `ADMIN_TOTP_SECRET` is set correctly in `.env`

### "Admin token required"

- You need to log in first
- Token is stored in session storage (cleared when browser closes)
- Click "Logout" and log in again

### Setup endpoint not working

- Make sure backend is running
- Check that `ADMIN_TOTP_SECRET` is set in `.env`
- Verify the secret is a valid base32 string

### QR code not scanning

- Ensure the QR code image is displayed correctly
- Try zooming in/out on the QR code
- Use manual entry as alternative
- Make sure Google Authenticator has camera permissions

### Admin actions appearing in revenue

- Check that `is_admin_action` column exists in transactions table
- Run the migration script: `python migrate_admin_tables.py`
- Verify admin actions have `is_admin_action=True`

### Word views not tracking

- Check that `word_views` table exists
- Run the migration script if needed
- Views are logged async - errors won't fail requests
- Check error logs for view logging failures

## Security Best Practices

1. **Never commit `.env` files**
   - Add to `.gitignore`
   - Never share TOTP secret

2. **Disable setup endpoint in production**
   - Remove route after initial setup
   - Or add IP whitelist

3. **Use HTTPS in production**
   - Required for secure token transmission
   - Configure SSL certificates

4. **Monitor admin access**
   - Review error logs regularly
   - Watch for suspicious activity

5. **Backup TOTP secret**
   - Store securely (password manager)
   - If lost, generate new secret and rescan QR code

6. **Rate limiting**
   - Already configured (10/min for login)
   - Adjust in `app/routes/admin.py` if needed

7. **Rotate secrets periodically**
   - Generate new TOTP secret
   - Update `.env`
   - Rescan QR code in Google Authenticator

## Admin Actions vs Real Purchases

### Real Purchases (`is_admin_action=false`)
- Created by actual users through payment flow
- Count towards revenue statistics
- Visible in public transaction history
- Real money collected via Stripe

### Admin Actions (`is_admin_action=true`)
- Created by admin panel word resets
- **Do NOT count** towards revenue statistics
- **Do NOT appear** in public transaction history
- Used for moderation/corrections
- Marked as "ADMIN_RESET" if no owner specified

### Example Scenario

1. User purchases "hello" for $5.00
   - Transaction: `is_admin_action=false`
   - Shows in income stats: ✅
   - Shows in public history: ✅

2. Admin resets "hello" to $1.00
   - Transaction: `is_admin_action=true`
   - Shows in income stats: ❌
   - Shows in public history: ❌

3. Revenue reports show: $5.00 (only real purchase)

## Frontend Integration

The admin panel is a separate Next.js app at `/admin/*`:

- `/admin/login` - TOTP login page
- `/admin/dashboard` - Main admin dashboard

Token is stored in browser session storage (cleared on browser close).

## Mobile Access

You can access the admin panel from mobile devices:

1. Visit the admin URL on your phone
2. Enter TOTP code from Google Authenticator
3. Dashboard is responsive and mobile-friendly

## Backup & Recovery

If you lose access:

1. **Lost phone with Google Authenticator:**
   - Generate new TOTP secret
   - Update `ADMIN_TOTP_SECRET` in `.env`
   - Restart backend
   - Visit `/api/admin/setup` for new QR code
   - Scan with new device

2. **Forgot TOTP secret:**
   - Check `backend/.env` file
   - Secret is stored there as `ADMIN_TOTP_SECRET`

## Future Enhancements

Potential improvements:

- Multiple admin accounts with different TOTP secrets
- Admin action audit log
- Email alerts for critical errors
- Dashboard filters (date ranges, error types)
- Export data to CSV
- Two-factor authentication with backup codes
- Admin permission levels (read-only, full access)

## Support

For issues with the admin system:

1. Check error logs in dashboard
2. Review backend console output
3. Verify TOTP secret is configured
4. Ensure database migration was run
5. Check browser console for frontend errors

## API Rate Limits

- Login: 10 requests per minute
- Setup: 5 requests per minute
- All other admin endpoints: Inherit default rate limits

## Deployment Notes

When deploying to production:

1. ✅ Set strong `ADMIN_TOTP_SECRET`
2. ✅ Run `migrate_admin_tables.py`
3. ✅ Disable or protect `/api/admin/setup` endpoint
4. ✅ Use HTTPS
5. ✅ Configure CORS properly
6. ✅ Monitor error logs regularly
7. ✅ Backup database (includes admin tables)

---

**Remember:** The TOTP secret is like a password - keep it secure and never commit it to version control!
