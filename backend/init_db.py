"""
Database initialization script.
Creates all tables defined in models.py
"""
from app.database import engine, Base
from app.models import Word, Transaction, ErrorLog, WordView, MessageReport


def init_db():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    print("\nTables created:")
    print("  - words")
    print("  - transactions")
    print("  - error_logs")
    print("  - word_views")
    print("  - message_reports")


if __name__ == "__main__":
    init_db()
