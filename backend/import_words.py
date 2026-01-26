"""
Word import script.
Reads words from ../words-raw/20k.txt and imports them into the database.
"""
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.database import SessionLocal
from app.models import Word


def import_words(file_path: str, batch_size: int = 1000):
    """
    Import words from a text file into the database.

    Args:
        file_path: Path to the text file containing words (one per line)
        batch_size: Number of words to insert per batch
    """
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    print(f"Reading words from: {file_path}")

    # Read all words from file
    with open(file_path, 'r', encoding='utf-8') as f:
        words = [line.strip().lower() for line in f if line.strip()]

    print(f"Found {len(words)} words to import")

    # Remove duplicates while preserving order
    unique_words = list(dict.fromkeys(words))
    print(f"Unique words after deduplication: {len(unique_words)}")

    # Import in batches
    db: Session = SessionLocal()
    try:
        imported = 0
        skipped = 0

        for i in range(0, len(unique_words), batch_size):
            batch = unique_words[i:i + batch_size]

            # Prepare batch data
            word_data = [
                {
                    "text": word,
                    "price": 1.00,
                    "owner_name": None,
                    "owner_message": None,
                    "lockout_ends_at": None
                }
                for word in batch
            ]

            # Use PostgreSQL's INSERT ... ON CONFLICT DO NOTHING
            stmt = insert(Word).values(word_data)
            stmt = stmt.on_conflict_do_nothing(index_elements=['text'])

            result = db.execute(stmt)
            db.commit()

            batch_imported = result.rowcount
            imported += batch_imported
            skipped += len(batch) - batch_imported

            print(f"Progress: {i + len(batch)}/{len(unique_words)} | Imported: {imported} | Skipped: {skipped}")

        print(f"\n✓ Import completed successfully!")
        print(f"  Total imported: {imported}")
        print(f"  Already existed (skipped): {skipped}")

    except Exception as e:
        print(f"\n✗ Error during import: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    # Default to the 20k.txt file
    words_file = Path(__file__).parent.parent / "words-raw" / "20k.txt"
    import_words(str(words_file))
