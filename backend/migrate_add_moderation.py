"""
Migration script to add message reporting and moderation features.
Adds new columns to words table and creates message_reports table.
"""
import psycopg2
from app.config import get_settings

settings = get_settings()

# Parse database URL
# Format: postgresql://user:password@host:port/database
db_url = settings.database_url.replace('postgresql://', '')
parts = db_url.split('@')
user_pass = parts[0].split(':')
host_db = parts[1].split('/')
host_port = host_db[0].split(':')

DB_CONFIG = {
    'user': user_pass[0],
    'password': user_pass[1],
    'host': host_port[0],
    'port': host_port[1],
    'database': host_db[1]
}

def run_migration():
    """Run the migration to add moderation columns and table."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        print("Starting migration...")

        # 1. Add moderation columns to words table
        print("Adding moderation_status column to words table...")
        cur.execute("""
            ALTER TABLE words
            ADD COLUMN IF NOT EXISTS moderation_status VARCHAR(20);
        """)

        print("Adding moderated_at column to words table...")
        cur.execute("""
            ALTER TABLE words
            ADD COLUMN IF NOT EXISTS moderated_at TIMESTAMP WITH TIME ZONE;
        """)

        # 2. Add index for moderation_status
        print("Creating index on moderation_status...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_words_moderation_status
            ON words(moderation_status);
        """)

        # 3. Create message_reports table
        print("Creating message_reports table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS message_reports (
                id SERIAL PRIMARY KEY,
                word_id INTEGER NOT NULL REFERENCES words(id),
                ip_address VARCHAR(45),
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
        """)

        # 4. Create indexes for message_reports
        print("Creating indexes on message_reports...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_message_reports_word_id
            ON message_reports(word_id);
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_message_reports_timestamp
            ON message_reports(timestamp);
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_message_reports_ip_word
            ON message_reports(ip_address, word_id);
        """)

        # Commit all changes
        conn.commit()
        print("\nMigration completed successfully!")
        print("\nAdded:")
        print("  - words.moderation_status column")
        print("  - words.moderated_at column")
        print("  - message_reports table")
        print("  - All necessary indexes")

    except Exception as e:
        conn.rollback()
        print(f"\nMigration failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
