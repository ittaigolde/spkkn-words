"""
RESTORE FROM BACKUP SCRIPT
===========================

⚠️  CAUTION: This script will restore database from a backup ⚠️

This script will:
1. List available backups
2. Show backup details and statistics
3. Restore word states (prices, owners, messages, lockouts)
4. Restore transactions (with corrected word IDs)
5. Restore error logs
6. Restore word views (with corrected word IDs)

IMPORTANT NOTES:
- Words are matched by text (word.text field)
- If a word doesn't exist in current database, it will be created
- Transaction and view IDs will be different (auto-increment)
- This does NOT delete current data, it adds/updates from backup

Usage:
    python restore_from_backup.py
"""

import os
import json
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine
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

# Confirmation word (must type exactly)
CONFIRMATION_WORD = "RESTORE"


def print_warning(message: str):
    """Print a warning message in red."""
    print(f"{RED}{BOLD}{message}{END}")


def print_info(message: str):
    """Print an info message in blue."""
    print(f"{BLUE}{message}{END}")


def print_success(message: str):
    """Print a success message in green."""
    print(f"{GREEN}{message}{END}")


def list_available_backups() -> list:
    """
    List all available backup directories.

    Returns:
        List of (path, timestamp, summary_data) tuples
    """
    backup_root = Path(__file__).parent / "backups"

    if not backup_root.exists():
        return []

    backups = []
    for backup_dir in sorted(backup_root.iterdir(), reverse=True):
        if backup_dir.is_dir() and backup_dir.name.startswith("factory_reset_"):
            summary_file = backup_dir / "summary.json"
            if summary_file.exists():
                try:
                    with open(summary_file, 'r') as f:
                        summary = json.load(f)
                    backups.append((backup_dir, summary))
                except Exception:
                    pass

    return backups


def display_backup_info(backup_dir: Path, summary: dict):
    """Display detailed information about a backup."""
    print(f"\n{BOLD}Backup Location:{END} {backup_dir}")
    print(f"{BOLD}Reset Date:{END} {summary.get('reset_date', 'Unknown')}")
    print(f"{BOLD}Database:{END} {summary.get('database_url', 'Unknown')}")

    counts = summary.get('counts', {})
    print(f"\n{BOLD}Data in Backup:{END}")
    print(f"  • Words: {counts.get('words', 0)}")
    print(f"  • Transactions: {counts.get('transactions', 0)}")
    print(f"  • Error logs: {counts.get('error_logs', 0)}")
    print(f"  • Word views: {counts.get('word_views', 0)}")

    stats = summary.get('statistics', {})
    print(f"\n{BOLD}Statistics:{END}")
    print(f"  • Total revenue: ${stats.get('total_revenue', 0):.2f}")
    print(f"  • Real transactions: {stats.get('real_transactions', 0)}")
    print(f"  • Admin actions: {stats.get('admin_actions', 0)}")
    print(f"  • Words with owners: {stats.get('words_with_owners', 0)}")
    print(f"  • Total views: {stats.get('total_views', 0)}")


def restore_from_backup(backup_dir: Path):
    """
    Restore database from a backup directory.

    Args:
        backup_dir: Path to backup directory
    """
    print_info("\n🔄 Starting restore process...\n")

    # Load backup files
    print_info("  - Loading backup files...")

    with open(backup_dir / "word_states.json", 'r') as f:
        word_states = json.load(f)

    with open(backup_dir / "transactions.json", 'r') as f:
        transactions = json.load(f)

    with open(backup_dir / "error_logs.json", 'r') as f:
        error_logs = json.load(f)

    with open(backup_dir / "word_views.json", 'r') as f:
        word_views = json.load(f)

    print_success(f"    ✓ Loaded all backup files")

    with Session(engine) as session:
        # Step 1: Restore word states
        print_info("\n  - Restoring word states...")
        word_id_mapping = {}  # old_id -> new_id
        restored_words = 0
        created_words = 0

        for word_state in word_states:
            old_id = word_state['id']
            text = word_state['text']

            # Find or create word
            word = session.query(Word).filter(Word.text == text).first()
            if not word:
                # Create new word if it doesn't exist
                word = Word(
                    text=text,
                    price=word_state['price'],
                    owner_name=word_state['owner_name'],
                    owner_message=word_state['owner_message'],
                    lockout_ends_at=datetime.fromisoformat(word_state['lockout_ends_at']) if word_state['lockout_ends_at'] else None
                )
                session.add(word)
                session.flush()
                created_words += 1
            else:
                # Update existing word
                word.price = word_state['price']
                word.owner_name = word_state['owner_name']
                word.owner_message = word_state['owner_message']
                word.lockout_ends_at = datetime.fromisoformat(word_state['lockout_ends_at']) if word_state['lockout_ends_at'] else None
                restored_words += 1

            word_id_mapping[old_id] = word.id

        session.commit()
        print_success(f"    ✓ Restored {restored_words} words, created {created_words} new words")

        # Step 2: Restore transactions
        print_info("  - Restoring transactions...")
        restored_transactions = 0
        skipped_transactions = 0

        for transaction in transactions:
            old_word_id = transaction['word_id']
            new_word_id = word_id_mapping.get(old_word_id)

            if new_word_id:
                new_transaction = Transaction(
                    word_id=new_word_id,
                    buyer_name=transaction['buyer_name'],
                    price_paid=transaction['price_paid'],
                    is_admin_action=transaction['is_admin_action'],
                    timestamp=datetime.fromisoformat(transaction['timestamp'])
                )
                session.add(new_transaction)
                restored_transactions += 1
            else:
                skipped_transactions += 1

        session.commit()
        print_success(f"    ✓ Restored {restored_transactions} transactions")
        if skipped_transactions > 0:
            print_warning(f"    ⚠ Skipped {skipped_transactions} transactions (word not found)")

        # Step 3: Restore error logs
        print_info("  - Restoring error logs...")
        restored_errors = 0

        for error_log in error_logs:
            new_error = ErrorLog(
                error_type=error_log['error_type'],
                error_message=error_log['error_message'],
                stack_trace=error_log['stack_trace'],
                endpoint=error_log['endpoint'],
                user_info=error_log['user_info'],
                timestamp=datetime.fromisoformat(error_log['timestamp'])
            )
            session.add(new_error)
            restored_errors += 1

        session.commit()
        print_success(f"    ✓ Restored {restored_errors} error logs")

        # Step 4: Restore word views
        print_info("  - Restoring word views...")
        restored_views = 0
        skipped_views = 0

        for view in word_views:
            old_word_id = view['word_id']
            new_word_id = word_id_mapping.get(old_word_id)

            if new_word_id:
                new_view = WordView(
                    word_id=new_word_id,
                    timestamp=datetime.fromisoformat(view['timestamp']),
                    ip_address=view['ip_address']
                )
                session.add(new_view)
                restored_views += 1
            else:
                skipped_views += 1

        session.commit()
        print_success(f"    ✓ Restored {restored_views} word views")
        if skipped_views > 0:
            print_warning(f"    ⚠ Skipped {skipped_views} views (word not found)")

    print_success("\n✅ Restore complete!\n")


def main():
    """Main execution flow."""
    print("\n" + "="*70)
    print_info("                    📦 RESTORE FROM BACKUP 📦")
    print("="*70)

    print_warning("\nWARNING: This will restore data from a backup.")
    print_warning("This will UPDATE existing words and ADD historical data.")
    print()

    # List available backups
    print_info("Searching for backups...\n")
    backups = list_available_backups()

    if not backups:
        print_warning("No backups found in backups/ directory.")
        print_info("Backups are created by the factory_reset.py script.\n")
        sys.exit(0)

    print_success(f"Found {len(backups)} backup(s):\n")

    # Display backups
    for i, (backup_dir, summary) in enumerate(backups, 1):
        print(f"{BOLD}{i}.{END} {backup_dir.name}")
        print(f"   Date: {summary.get('reset_date', 'Unknown')}")
        print(f"   Words: {summary.get('counts', {}).get('words', 0)}, "
              f"Transactions: {summary.get('counts', {}).get('transactions', 0)}")
        print()

    # Select backup
    print(f"{BOLD}Select a backup to restore:{END}")
    try:
        selection = input("Enter backup number (or 'q' to quit): ").strip()
        if selection.lower() == 'q':
            print_info("\nRestore cancelled.\n")
            sys.exit(0)

        backup_index = int(selection) - 1
        if backup_index < 0 or backup_index >= len(backups):
            print_warning("\nInvalid selection. Restore cancelled.\n")
            sys.exit(0)

        selected_backup, summary = backups[backup_index]
    except (ValueError, IndexError):
        print_warning("\nInvalid input. Restore cancelled.\n")
        sys.exit(0)

    # Show selected backup details
    print("\n" + "-"*70)
    print_info("\nSelected Backup Details:")
    display_backup_info(selected_backup, summary)
    print("\n" + "-"*70)

    print_warning("\n⚠️  What will happen:")
    print("  1. Word states will be restored (prices, owners, messages, lockouts)")
    print("  2. Transactions will be restored (IDs will be different)")
    print("  3. Error logs will be restored")
    print("  4. Word views will be restored")
    print("  5. Existing data will be UPDATED/MERGED (not deleted)")

    # Confirmation
    print(f"\n{BOLD}CONFIRMATION REQUIRED{END}")
    print(f"To proceed with restore, type the word: {YELLOW}{BOLD}{CONFIRMATION_WORD}{END}")
    response = input("Type here: ").strip()

    if response != CONFIRMATION_WORD:
        print_info("\n❌ Confirmation failed. Restore cancelled.")
        print_info("Nothing was changed.\n")
        sys.exit(0)

    print_success("\n✓ Confirmation accepted.")
    print_warning("\n⚠️  PROCEEDING WITH RESTORE ⚠️\n")

    # Perform restore
    try:
        restore_from_backup(selected_backup)
    except Exception as e:
        print_warning(f"\n❌ ERROR: Restore failed: {e}")
        print_warning("Database may be in an inconsistent state.")
        sys.exit(1)

    print("\n" + "="*70)
    print_success("                     ✅ RESTORE COMPLETE ✅")
    print("="*70)
    print(f"\n✓ Data restored from: {BOLD}{selected_backup.name}{END}")
    print("\nYour database has been restored from the backup.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_info("\n\n❌ Restore cancelled by user (Ctrl+C)")
        print_info("Nothing was changed.\n")
        sys.exit(0)
    except Exception as e:
        print_warning(f"\n❌ Unexpected error: {e}")
        print_warning("Restore may be incomplete. Check your database state.")
        sys.exit(1)
