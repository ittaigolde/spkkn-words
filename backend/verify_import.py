"""
Quick verification script to check word import.
"""
from app.database import SessionLocal
from app.models import Word

db = SessionLocal()

try:
    total_words = db.query(Word).count()
    print(f"✓ Total words in database: {total_words}")

    # Show a few sample words
    sample_words = db.query(Word).limit(5).all()
    print("\nSample words:")
    for word in sample_words:
        print(f"  - {word.text} (${word.price})")

finally:
    db.close()
