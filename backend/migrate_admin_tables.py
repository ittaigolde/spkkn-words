"""
Database migration script to add admin features.

Adds:
- is_admin_action column to transactions table
- error_logs table
- word_views table

Run this script ONCE to upgrade your existing database.
"""
from sqlalchemy import create_engine, text
from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)


def migrate():
    """Run migration."""
    print("Starting database migration for admin features...")

    with engine.begin() as conn:
        # 1. Add is_admin_action column to transactions
        print("1. Adding is_admin_action column to transactions...")
        try:
            conn.execute(text("""
                ALTER TABLE transactions
                ADD COLUMN is_admin_action BOOLEAN DEFAULT FALSE NOT NULL;
            """))
            print("   ✓ Column added")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("   ⚠ Column already exists, skipping")
            else:
                raise

        # 2. Create index on is_admin_action
        print("2. Creating index on is_admin_action...")
        try:
            conn.execute(text("""
                CREATE INDEX idx_transactions_is_admin_action
                ON transactions(is_admin_action);
            """))
            print("   ✓ Index created")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("   ⚠ Index already exists, skipping")
            else:
                raise

        # 3. Create error_logs table
        print("3. Creating error_logs table...")
        try:
            conn.execute(text("""
                CREATE TABLE error_logs (
                    id SERIAL PRIMARY KEY,
                    error_type VARCHAR(100) NOT NULL,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT,
                    endpoint VARCHAR(200),
                    user_info VARCHAR(200),
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
                );
            """))
            print("   ✓ Table created")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("   ⚠ Table already exists, skipping")
            else:
                raise

        # 4. Create indexes on error_logs
        print("4. Creating indexes on error_logs...")
        try:
            conn.execute(text("""
                CREATE INDEX idx_error_logs_timestamp ON error_logs(timestamp);
            """))
            conn.execute(text("""
                CREATE INDEX idx_error_logs_error_type ON error_logs(error_type);
            """))
            print("   ✓ Indexes created")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("   ⚠ Indexes already exist, skipping")
            else:
                raise

        # 5. Create word_views table
        print("5. Creating word_views table...")
        try:
            conn.execute(text("""
                CREATE TABLE word_views (
                    id SERIAL PRIMARY KEY,
                    word_id INTEGER NOT NULL REFERENCES words(id),
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    ip_address VARCHAR(45)
                );
            """))
            print("   ✓ Table created")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("   ⚠ Table already exists, skipping")
            else:
                raise

        # 6. Create indexes on word_views
        print("6. Creating indexes on word_views...")
        try:
            conn.execute(text("""
                CREATE INDEX idx_word_views_word_id ON word_views(word_id);
            """))
            conn.execute(text("""
                CREATE INDEX idx_word_views_timestamp ON word_views(timestamp);
            """))
            print("   ✓ Indexes created")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("   ⚠ Indexes already exist, skipping")
            else:
                raise

    print("\n✅ Migration completed successfully!")
    print("\nNext steps:")
    print("1. Generate TOTP secret: python -c \"import pyotp; print(pyotp.random_base32())\"")
    print("2. Add ADMIN_TOTP_SECRET to your .env file")
    print("3. Visit /api/admin/setup to get QR code for Google Authenticator")
    print("4. Restart your backend server")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        raise
