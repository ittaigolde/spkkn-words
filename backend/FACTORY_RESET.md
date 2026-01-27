# Factory Reset Script

## ⚠️ WARNING: DESTRUCTIVE OPERATION ⚠️

This script resets your database to factory-fresh state. **Use with extreme caution!**

## What It Does

### Backs Up (Preserves)
- ✅ All transactions (exported to JSON)
- ✅ All word states (exported to JSON)
- ✅ All error logs (exported to JSON)
- ✅ All word views (exported to JSON)
- ✅ Statistics summary

### Resets (Modifies)
- 🔄 All words reset to $1.00
- 🔄 All ownership cleared (no owners)
- 🔄 All lockouts removed
- 🔄 Word list remains intact (only states reset)

### Deletes (Removes)
- ❌ All transactions (but backed up)
- ❌ All error logs (but backed up)
- ❌ All word views (but backed up)

## When to Use

**Appropriate Uses:**
- ✅ Development/testing environment resets
- ✅ Starting fresh after testing
- ✅ Demo/staging database cleanup
- ✅ Emergency recovery from corruption
- ✅ QA testing cycles

**DO NOT USE FOR:**
- ❌ Production with real user data (without explicit consent)
- ❌ Routine maintenance
- ❌ Fixing individual records (use admin panel instead)

## Safety Features

### Two-Factor Confirmation
1. **First confirmation:** Type `RESET` (exact, case-sensitive)
2. **Second confirmation:** Type `ERASE` (exact, case-sensitive)

Not `y` or `yes` - must type exact 5-letter words.

### Automatic Backup
Before any changes, all data is exported to:
```
backups/factory_reset_YYYYMMDD_HHMMSS/
├── transactions.json      (All transaction history)
├── word_states.json       (All word ownership states)
├── error_logs.json        (All error logs)
├── word_views.json        (All analytics data)
└── summary.json           (Statistics snapshot)
```

### Abort Points
- Press `Ctrl+C` at any time before second confirmation
- Type anything except exact confirmation words
- Database remains unchanged if aborted

## Usage

### Prerequisites

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### Run Script

```bash
python factory_reset.py
```

### Interactive Process

```
1. Script shows current database statistics
2. Explains what will happen
3. First confirmation: Type "RESET"
4. Second confirmation: Type "ERASE"
5. Exports all data to timestamped backup
6. Performs factory reset
7. Shows new statistics
8. Displays backup location
```

## Example Output

```
======================================================================
                    ⚠️  FACTORY RESET SCRIPT ⚠️
======================================================================

WARNING: This script will permanently reset your database!
This action is IRREVERSIBLE and should only be used for:
  • Development/testing environments
  • Starting fresh after testing
  • Emergency recovery scenarios

DO NOT USE IN PRODUCTION WITH REAL USER DATA!

📊 Current Database Statistics:
   • Total words: 20000
   • Words with owners: 1234
   • Transactions: 5678
   • Error logs: 42
   • Word views: 98765
   • Total revenue: $12345.67

----------------------------------------------------------------------

What will happen:
  1. ✓ All data will be backed up to timestamped files
  2. ✗ All transactions will be deleted (but saved in backup)
  3. ✗ All error logs will be deleted (but saved in backup)
  4. ✗ All word views will be deleted (but saved in backup)
  5. 🔄 All words will be reset to $1.00 with no owners
  6. ✓ Word list will remain (only ownership/prices reset)
----------------------------------------------------------------------


FIRST CONFIRMATION
To proceed, type the word: RESET
Type here: RESET

✓ First confirmation accepted.

Data will be backed up before any changes are made.

SECOND CONFIRMATION
This is your LAST CHANCE to abort!
To confirm factory reset, type the word: ERASE
Type here: ERASE

✓ Second confirmation accepted.

⚠️  PROCEEDING WITH FACTORY RESET ⚠️

📦 Exporting data to: backups/factory_reset_20260126_143022/
  - Exporting transactions...
    ✓ Exported 5678 transactions
  - Exporting word states...
    ✓ Exported 20000 word states
  - Exporting error logs...
    ✓ Exported 42 error logs
  - Exporting word views...
    ✓ Exported 98765 word views
    ✓ Created summary file

✅ All data exported to: backups/factory_reset_20260126_143022/

🔄 Performing factory reset...

  - Deleting word views...
    ✓ Deleted 98765 word views
  - Deleting error logs...
    ✓ Deleted 42 error logs
  - Deleting transactions...
    ✓ Deleted 5678 transactions
  - Resetting all words to $1.00...
    ✓ Reset 20000 words to factory defaults

✅ Factory reset complete!

📊 New Database Statistics (After Reset):
   • Total words: 20000
   • Words with owners: 0
   • Transactions: 0
   • Error logs: 0
   • Word views: 0
   • Total revenue: $0.00

======================================================================
                  ✅ FACTORY RESET COMPLETE ✅
======================================================================

📦 Your data backup is saved at: backups/factory_reset_20260126_143022/

What happened:
  ✓ All data backed up
  ✓ All words reset to $1.00
  ✓ All ownership cleared
  ✓ All lockouts removed
  ✓ All transactions deleted (but backed up)
  ✓ All logs deleted (but backed up)

Your database is now in factory-fresh state!
To restore from backup, use the files in: backups/factory_reset_20260126_143022/
```

## Backup Files Format

### transactions.json
```json
[
  {
    "id": 1,
    "word_id": 42,
    "buyer_name": "Alice",
    "price_paid": 5.0,
    "timestamp": "2026-01-26T14:30:22.123456",
    "is_admin_action": false
  }
]
```

### word_states.json
```json
[
  {
    "id": 1,
    "text": "hello",
    "price": 5.0,
    "owner_name": "Alice",
    "owner_message": "Hello world!",
    "lockout_ends_at": "2026-01-26T19:30:22.123456",
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-26T14:30:22.123456"
  }
]
```

### summary.json
```json
{
  "reset_timestamp": "20260126_143022",
  "reset_date": "2026-01-26T14:30:22.123456",
  "database_url": "localhost:5432/word_registry",
  "counts": {
    "transactions": 5678,
    "words": 20000,
    "error_logs": 42,
    "word_views": 98765
  },
  "statistics": {
    "total_revenue": 12345.67,
    "admin_actions": 12,
    "real_transactions": 5666,
    "words_with_owners": 1234,
    "total_views": 98765
  }
}
```

## Restoring from Backup

### Manual Restoration

1. **Restore word states:**
   ```python
   import json
   from app.models import Word
   from app.database import SessionLocal

   with open('backups/factory_reset_TIMESTAMP/word_states.json') as f:
       states = json.load(f)

   db = SessionLocal()
   for state in states:
       word = db.query(Word).filter(Word.text == state['text']).first()
       if word:
           word.price = state['price']
           word.owner_name = state['owner_name']
           word.owner_message = state['owner_message']
           # ... etc
   db.commit()
   ```

2. **Restore transactions:**
   - Transactions have auto-increment IDs, so you'd need to restore carefully
   - Consider if you actually need transaction history or just word states

3. **Alternative: Database backup/restore**
   - Use PostgreSQL's pg_dump/pg_restore for full restoration
   - Backup files are for reference/audit, not full restoration

## After Reset

### What You'll See

**Frontend:**
- All words show $1.00 price
- No words have owners
- All words are available
- Transaction history is empty

**Admin Dashboard:**
- Total income: $0.00
- No transactions
- No error logs
- No word views

**Database:**
- `words` table: All prices = 1.00, no owners, no lockouts
- `transactions` table: Empty
- `error_logs` table: Empty
- `word_views` table: Empty

### Next Steps

1. Verify reset completed successfully
2. Test basic functionality (word purchase)
3. Verify Stripe integration still works
4. Check admin panel accessibility

## Cancelling Reset

### Before Confirmations
- Type anything except exact confirmation words
- Press `Ctrl+C`
- Close terminal

### After First Confirmation
- Type anything except "ERASE" for second confirmation
- Press `Ctrl+C`

### After Second Confirmation
- **TOO LATE** - export starts immediately
- Press `Ctrl+C` during export (database unchanged)
- Once export completes, reset proceeds automatically

### After Reset Starts
- **CANNOT ABORT** - reset is in progress
- Data is backed up, but reset will complete
- Use backup files to restore if needed

## Troubleshooting

### "Database connection failed"
- Check DATABASE_URL in .env
- Ensure PostgreSQL is running
- Verify credentials

### "Permission denied" on backup directory
- Check write permissions on `backups/` folder
- Run script with appropriate user permissions

### "Reset failed partway through"
- Check backup files - data is safe
- Check database state: `python verify_import.py`
- May need to manually complete reset or restore

### "Want to undo reset"
- Use backup files in `backups/factory_reset_TIMESTAMP/`
- Manually restore data (see "Restoring from Backup")
- Or restore from PostgreSQL backup if available

## Best Practices

### Before Running

1. ✅ Verify you're in correct environment (dev/staging, not production)
2. ✅ Check DATABASE_URL points to correct database
3. ✅ Ensure you have write permissions for `backups/` folder
4. ✅ Consider PostgreSQL backup: `pg_dump word_registry > pre_reset.sql`
5. ✅ Notify team members (if shared database)

### After Running

1. ✅ Verify backup files exist and are readable
2. ✅ Test basic functionality
3. ✅ Check admin panel works
4. ✅ Archive backup files for record-keeping
5. ✅ Document why reset was performed

### Production Use

**If you absolutely must reset production:**

1. 🔴 Get explicit user consent (GDPR/data regulations)
2. 🔴 Announce maintenance window
3. 🔴 Take full PostgreSQL backup first
4. 🔴 Download backup files to safe location
5. 🔴 Document legal/compliance requirements
6. 🔴 Notify users of data deletion
7. 🔴 Consider partial reset (specific words) via admin panel instead

## Security Notes

- Backup files contain all user data (names, messages, IPs)
- Store backups securely, don't commit to git
- Add `backups/` to `.gitignore`
- Delete old backups per data retention policy
- Backup files are plain JSON (no encryption)

## Support

If you encounter issues:

1. Check backup files exist
2. Check database state with `verify_import.py`
3. Review error messages carefully
4. Check PostgreSQL logs: `sudo journalctl -u postgresql`
5. Restore from PostgreSQL backup if necessary: `pg_restore pre_reset.sql`

## FAQ

**Q: Can I undo a factory reset?**
A: Not automatically. You'll need to manually restore from the backup JSON files or from a PostgreSQL backup.

**Q: Will this delete the words themselves?**
A: No. The 20,000 words remain in the database. Only ownership, prices, and transaction history are reset.

**Q: What if I accidentally run this in production?**
A: The backup files are created BEFORE any changes. Restore from those files or from your PostgreSQL backup.

**Q: Can I reset just one word?**
A: Yes, use the admin panel's "Reset Word" feature instead. This script is for resetting everything.

**Q: How long does it take?**
A: Usually 10-30 seconds depending on database size. Most time is spent exporting data.

**Q: Where are backups stored?**
A: `backend/backups/factory_reset_TIMESTAMP/` (timestamped folders)

**Q: Should I commit backups to git?**
A: NO! Backups contain user data. Add `backups/` to `.gitignore`.

---

**Remember: This is a destructive operation. Always verify you're in the correct environment before proceeding!**
