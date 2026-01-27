"""
FACTORY RESET SCRIPT
====================

⚠️  DANGER: This script will reset the entire database to factory defaults ⚠️

This script will:
1. Export ALL data to timestamped backup files (transactions, word states, logs)
2. DELETE all transactions (but saved in backup)
3. DELETE all error logs (but saved in backup)
4. DELETE all word views (but saved in backup)
5. DELETE all words (but saved in backup)
6. RE-IMPORT original 20,000 words from 20k.txt

This is IRREVERSIBLE. Only use this for:
- Development/testing resets
- Starting fresh after testing
- Emergency database corruption recovery

DO NOT USE IN PRODUCTION WITH REAL USER DATA WITHOUT EXPLICIT CONSENT.

Usage:
    python factory_reset.py
"""

import os
import json
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
import sys

from app.config import get_settings
from app.models import Word, Transaction, ErrorLog, WordView

settings = get_settings()
engine = create_engine(settings.database_url)

# Colors for terminal output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
END = '\033[0m'

# Confirmation words (must type exactly)
FIRST_CONFIRMATION = "RESET"
SECOND_CONFIRMATION = "ERASE"


def print_warning(message: str):
    """Print a warning message in red."""
    print(f"{RED}{BOLD}{message}{END}")


def print_info(message: str):
    """Print an info message in blue."""
    print(f"{BLUE}{message}{END}")


def print_success(message: str):
    """Print a success message in green."""
    print(f"{GREEN}{message}{END}")


def export_data_to_backup() -> str:
    """
    Export all data to timestamped backup files.

    Returns:
        Path to backup directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/factory_reset_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)

    print_info(f"\n📦 Exporting data to: {backup_dir}/")

    with Session(engine) as session:
        # Export transactions
        print_info("  - Exporting transactions...")
        transactions = session.query(Transaction).all()
        transactions_data = [
            {
                "id": t.id,
                "word_id": t.word_id,
                "buyer_name": t.buyer_name,
                "price_paid": float(t.price_paid),
                "timestamp": t.timestamp.isoformat(),
                "is_admin_action": t.is_admin_action
            }
            for t in transactions
        ]
        with open(f"{backup_dir}/transactions.json", "w") as f:
            json.dump(transactions_data, f, indent=2)
        print_success(f"    ✓ Exported {len(transactions_data)} transactions")

        # Export word states
        print_info("  - Exporting word states...")
        words = session.query(Word).all()
        words_data = [
            {
                "id": w.id,
                "text": w.text,
                "price": float(w.price),
                "owner_name": w.owner_name,
                "owner_message": w.owner_message,
                "lockout_ends_at": w.lockout_ends_at.isoformat() if w.lockout_ends_at else None,
                "created_at": w.created_at.isoformat(),
                "updated_at": w.updated_at.isoformat()
            }
            for w in words
        ]
        with open(f"{backup_dir}/word_states.json", "w") as f:
            json.dump(words_data, f, indent=2)
        print_success(f"    ✓ Exported {len(words_data)} word states")

        # Export error logs
        print_info("  - Exporting error logs...")
        error_logs = session.query(ErrorLog).all()
        error_logs_data = [
            {
                "id": e.id,
                "error_type": e.error_type,
                "error_message": e.error_message,
                "stack_trace": e.stack_trace,
                "endpoint": e.endpoint,
                "user_info": e.user_info,
                "timestamp": e.timestamp.isoformat()
            }
            for e in error_logs
        ]
        with open(f"{backup_dir}/error_logs.json", "w") as f:
            json.dump(error_logs_data, f, indent=2)
        print_success(f"    ✓ Exported {len(error_logs_data)} error logs")

        # Export word views
        print_info("  - Exporting word views...")
        word_views = session.query(WordView).all()
        word_views_data = [
            {
                "id": v.id,
                "word_id": v.word_id,
                "timestamp": v.timestamp.isoformat(),
                "ip_address": v.ip_address
            }
            for v in word_views
        ]
        with open(f"{backup_dir}/word_views.json", "w") as f:
            json.dump(word_views_data, f, indent=2)
        print_success(f"    ✓ Exported {len(word_views_data)} word views")

        # Create summary
        summary = {
            "reset_timestamp": timestamp,
            "reset_date": datetime.now().isoformat(),
            "database_url": settings.database_url.split("@")[-1],  # Hide credentials
            "counts": {
                "transactions": len(transactions_data),
                "words": len(words_data),
                "error_logs": len(error_logs_data),
                "word_views": len(word_views_data)
            },
            "statistics": {
                "total_revenue": sum(float(t.price_paid) for t in transactions if not t.is_admin_action),
                "admin_actions": sum(1 for t in transactions if t.is_admin_action),
                "real_transactions": sum(1 for t in transactions if not t.is_admin_action),
                "words_with_owners": sum(1 for w in words if w.owner_name),
                "total_views": len(word_views_data)
            }
        }
        with open(f"{backup_dir}/summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        print_success(f"    ✓ Created summary file")

    print_success(f"\n✅ All data exported to: {backup_dir}/\n")
    return backup_dir


def reimport_original_words():
    """
    Re-import the original 20,000 words from 20k.txt.
    """
    words_file = Path(__file__).parent.parent / "words-raw" / "20k.txt"

    if not words_file.exists():
        raise FileNotFoundError(f"Original word list not found: {words_file}")

    print_info(f"  - Reading original words from: {words_file.name}...")

    # Read all words from file
    with open(words_file, 'r', encoding='utf-8') as f:
        words = [line.strip().lower() for line in f if line.strip()]

    # Remove duplicates while preserving order
    unique_words = list(dict.fromkeys(words))
    print_success(f"    ✓ Loaded {len(unique_words)} unique words")

    # Import in batches
    print_info("  - Importing words into database...")
    batch_size = 1000
    imported = 0

    with Session(engine) as session:
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

            # Use PostgreSQL's INSERT
            stmt = insert(Word).values(word_data)
            result = session.execute(stmt)
            session.commit()

            imported += result.rowcount

        print_success(f"    ✓ Imported {imported} original words")


def perform_factory_reset():
    """
    Reset the database to factory defaults.
    Deletes everything and re-imports original words from 20k.txt.
    """
    print_info("\n🔄 Performing factory reset...\n")

    with Session(engine) as session:
        # Delete word views
        print_info("  - Deleting word views...")
        deleted_views = session.query(WordView).delete()
        session.commit()
        print_success(f"    ✓ Deleted {deleted_views} word views")

        # Delete error logs
        print_info("  - Deleting error logs...")
        deleted_errors = session.query(ErrorLog).delete()
        session.commit()
        print_success(f"    ✓ Deleted {deleted_errors} error logs")

        # Delete transactions
        print_info("  - Deleting transactions...")
        deleted_transactions = session.query(Transaction).delete()
        session.commit()
        print_success(f"    ✓ Deleted {deleted_transactions} transactions")

        # Delete ALL words (including user-created ones)
        print_info("  - Deleting all words...")
        deleted_words = session.query(Word).delete()
        session.commit()
        print_success(f"    ✓ Deleted {deleted_words} words")

    # Re-import original words from 20k.txt
    print_info("  - Re-importing original words...")
    try:
        reimport_original_words()
    except FileNotFoundError as e:
        raise Exception(f"Cannot complete factory reset: {e}")

    print_success("\n✅ Factory reset complete!\n")


def show_database_stats():
    """Show current database statistics."""
    with Session(engine) as session:
        word_count = session.query(Word).count()
        transaction_count = session.query(Transaction).count()
        error_count = session.query(ErrorLog).count()
        view_count = session.query(WordView).count()

        # Count words with owners
        owned_words = session.query(Word).filter(Word.owner_name.isnot(None)).count()

        # Calculate total revenue (excluding admin actions)
        result = session.query(Transaction).filter(Transaction.is_admin_action == False).all()
        total_revenue = sum(float(t.price_paid) for t in result)

        print_info("\n📊 Current Database Statistics:")
        print(f"   • Total words: {word_count}")
        print(f"   • Words with owners: {owned_words}")
        print(f"   • Transactions: {transaction_count}")
        print(f"   • Error logs: {error_count}")
        print(f"   • Word views: {view_count}")
        print(f"   • Total revenue: ${total_revenue:.2f}")


def main():
    """Main execution flow."""
    print("\n" + "="*70)
    print_warning("                    ⚠️  FACTORY RESET SCRIPT ⚠️")
    print("="*70)

    print_warning("\nWARNING: This script will permanently reset your database!")
    print_warning("This action is IRREVERSIBLE and should only be used for:")
    print("  • Development/testing environments")
    print("  • Starting fresh after testing")
    print("  • Emergency recovery scenarios")
    print()
    print_warning("DO NOT USE IN PRODUCTION WITH REAL USER DATA!\n")

    # Show current stats
    show_database_stats()

    print("\n" + "-"*70)
    print_warning("\nWhat will happen:")
    print("  1. ✓ All data will be backed up to timestamped files")
    print("  2. ✗ All transactions will be deleted (but saved in backup)")
    print("  3. ✗ All error logs will be deleted (but saved in backup)")
    print("  4. ✗ All word views will be deleted (but saved in backup)")
    print("  5. ✗ All words will be deleted (but saved in backup)")
    print("  6. ✓ Original 20,000 words will be re-imported from 20k.txt")
    print("-"*70 + "\n")

    # First confirmation
    print(f"\n{BOLD}FIRST CONFIRMATION{END}")
    print(f"To proceed, type the word: {YELLOW}{BOLD}{FIRST_CONFIRMATION}{END}")
    first_response = input("Type here: ").strip()

    if first_response != FIRST_CONFIRMATION:
        print_info("\n❌ Confirmation failed. Factory reset cancelled.")
        print_info("Nothing was changed.\n")
        sys.exit(0)

    print_success("\n✓ First confirmation accepted.")

    # Show backup location
    print(f"\n{BOLD}Data will be backed up before any changes are made.{END}")

    # Second confirmation
    print(f"\n{BOLD}SECOND CONFIRMATION{END}")
    print_warning("This is your LAST CHANCE to abort!")
    print(f"To confirm factory reset, type the word: {YELLOW}{BOLD}{SECOND_CONFIRMATION}{END}")
    second_response = input("Type here: ").strip()

    if second_response != SECOND_CONFIRMATION:
        print_info("\n❌ Confirmation failed. Factory reset cancelled.")
        print_info("Nothing was changed.\n")
        sys.exit(0)

    print_success("\n✓ Second confirmation accepted.")
    print_warning("\n⚠️  PROCEEDING WITH FACTORY RESET ⚠️\n")

    # Export data first
    try:
        backup_dir = export_data_to_backup()
    except Exception as e:
        print_warning(f"\n❌ ERROR: Failed to export data: {e}")
        print_warning("Factory reset aborted. Database unchanged.")
        sys.exit(1)

    # Perform reset
    try:
        perform_factory_reset()
    except Exception as e:
        print_warning(f"\n❌ ERROR: Factory reset failed: {e}")
        print_warning(f"Your data backup is safe at: {backup_dir}")
        print_warning("You may need to manually restore the database.")
        sys.exit(1)

    # Show new stats
    print_info("\n📊 New Database Statistics (After Reset):")
    show_database_stats()

    print("\n" + "="*70)
    print_success("                  ✅ FACTORY RESET COMPLETE ✅")
    print("="*70)
    print(f"\n📦 Your data backup is saved at: {BOLD}{backup_dir}/{END}")
    print("\nWhat happened:")
    print(f"  {GREEN}✓{END} All data backed up")
    print(f"  {GREEN}✓{END} All words deleted (including user-created)")
    print(f"  {GREEN}✓{END} Original 20,000 words re-imported")
    print(f"  {GREEN}✓{END} All transactions deleted (but backed up)")
    print(f"  {GREEN}✓{END} All logs deleted (but backed up)")
    print("\nYour database is now in factory-fresh state!")
    print(f"To restore from backup, use the files in: {backup_dir}/\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_info("\n\n❌ Factory reset cancelled by user (Ctrl+C)")
        print_info("Nothing was changed.\n")
        sys.exit(0)
    except Exception as e:
        print_warning(f"\n❌ Unexpected error: {e}")
        print_warning("Factory reset may be incomplete. Check your database state.")
        sys.exit(1)
