"""
Database initialization script.
Creates all tables defined in models.py
"""
from app.database import engine, Base
from app.models import Word, Transaction


def init_db():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")
    print("\nTables created:")
    print("  - words")
    print("  - transactions")


if __name__ == "__main__":
    init_db()
