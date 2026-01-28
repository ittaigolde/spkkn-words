"""
Admin service for analytics, error logging, and word management.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
import traceback

from .models import Word, Transaction, ErrorLog, WordView, MessageReport
from .utils import is_word_available
from .config import get_settings

settings = get_settings()


class AdminService:
    """Service for admin operations."""

    @staticmethod
    def log_error(
        db: Session,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        endpoint: Optional[str] = None,
        user_info: Optional[str] = None
    ) -> ErrorLog:
        """
        Log an error to the database.

        Args:
            db: Database session
            error_type: Type/category of error
            error_message: Error message
            stack_trace: Full stack trace (optional)
            endpoint: API endpoint where error occurred
            user_info: User IP or user agent

        Returns:
            ErrorLog instance
        """
        error_log = ErrorLog(
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            endpoint=endpoint,
            user_info=user_info
        )
        db.add(error_log)
        db.commit()
        db.refresh(error_log)
        return error_log

    @staticmethod
    def log_word_view(db: Session, word_id: int, ip_address: Optional[str] = None):
        """
        Log a word page view for analytics.

        Args:
            db: Database session
            word_id: ID of viewed word
            ip_address: User's IP address (optional)
        """
        view = WordView(word_id=word_id, ip_address=ip_address)
        db.add(view)
        db.commit()

    @staticmethod
    def get_income_stats(db: Session) -> dict:
        """
        Get income statistics (excluding admin actions).

        Returns:
            Dictionary with:
            - total_income: All-time revenue
            - today_income: Revenue from today
            - week_income: Revenue from last 7 days
            - total_transactions: Total number of real transactions
            - today_transactions: Transactions today
            - week_transactions: Transactions this week
        """
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        week_start = now - timedelta(days=7)

        # Total income (exclude admin actions)
        total_result = db.query(func.sum(Transaction.price_paid))\
            .filter(Transaction.is_admin_action == False)\
            .scalar()
        total_income = float(total_result) if total_result else 0.0

        # Today's income
        today_result = db.query(func.sum(Transaction.price_paid))\
            .filter(
                and_(
                    Transaction.is_admin_action == False,
                    Transaction.timestamp >= today_start
                )
            )\
            .scalar()
        today_income = float(today_result) if today_result else 0.0

        # Week income
        week_result = db.query(func.sum(Transaction.price_paid))\
            .filter(
                and_(
                    Transaction.is_admin_action == False,
                    Transaction.timestamp >= week_start
                )
            )\
            .scalar()
        week_income = float(week_result) if week_result else 0.0

        # Transaction counts
        total_transactions = db.query(Transaction)\
            .filter(Transaction.is_admin_action == False)\
            .count()

        today_transactions = db.query(Transaction)\
            .filter(
                and_(
                    Transaction.is_admin_action == False,
                    Transaction.timestamp >= today_start
                )
            )\
            .count()

        week_transactions = db.query(Transaction)\
            .filter(
                and_(
                    Transaction.is_admin_action == False,
                    Transaction.timestamp >= week_start
                )
            )\
            .count()

        return {
            "total_income": total_income,
            "today_income": today_income,
            "week_income": week_income,
            "total_transactions": total_transactions,
            "today_transactions": today_transactions,
            "week_transactions": week_transactions
        }

    @staticmethod
    def get_most_viewed_words(db: Session, limit: int = 20) -> list:
        """
        Get most viewed words in the last 30 days.

        Args:
            db: Database session
            limit: Number of results to return

        Returns:
            List of dictionaries with word info and view count
        """
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        # Query views grouped by word
        results = db.query(
            Word.text,
            Word.price,
            Word.owner_name,
            func.count(WordView.id).label('view_count')
        )\
            .join(WordView, Word.id == WordView.word_id)\
            .filter(WordView.timestamp >= thirty_days_ago)\
            .group_by(Word.id, Word.text, Word.price, Word.owner_name)\
            .order_by(func.count(WordView.id).desc())\
            .limit(limit)\
            .all()

        return [
            {
                "word": row.text,
                "price": float(row.price),
                "owner": row.owner_name,
                "views": row.view_count
            }
            for row in results
        ]

    @staticmethod
    def get_recent_errors(db: Session, limit: int = 50) -> list:
        """
        Get recent error logs.

        Args:
            db: Database session
            limit: Number of results to return

        Returns:
            List of error logs
        """
        errors = db.query(ErrorLog)\
            .order_by(ErrorLog.timestamp.desc())\
            .limit(limit)\
            .all()

        return [
            {
                "id": error.id,
                "type": error.error_type,
                "message": error.error_message,
                "stack_trace": error.stack_trace,
                "endpoint": error.endpoint,
                "user_info": error.user_info,
                "timestamp": error.timestamp.isoformat()
            }
            for error in errors
        ]

    @staticmethod
    def reset_word(
        db: Session,
        word_text: str,
        new_price: Decimal,
        owner_name: Optional[str] = None,
        owner_message: Optional[str] = None
    ) -> Word:
        """
        Admin override: Reset a word's price and optionally set owner.

        This creates a transaction marked as admin action (not counted in revenue).

        Args:
            db: Database session
            word_text: Word to reset
            new_price: New price for the word
            owner_name: New owner name (optional)
            owner_message: New owner message (optional)

        Returns:
            Updated Word instance

        Raises:
            ValueError: If word not found
        """
        word = db.query(Word).filter(Word.text == word_text.lower()).first()

        if not word:
            raise ValueError(f"Word '{word_text}' not found")

        # Store old values for transaction record
        old_price = word.price
        old_owner = word.owner_name or "None"

        # Update word
        word.price = new_price

        if owner_name is not None:
            word.owner_name = owner_name
            word.owner_message = owner_message

            # Set lockout based on new price
            lockout_hours = float(new_price)
            word.lockout_ends_at = datetime.now(timezone.utc) + timedelta(hours=lockout_hours)
        else:
            # Clear ownership if no owner specified
            word.owner_name = None
            word.owner_message = None
            word.lockout_ends_at = None

        # Create transaction record (marked as admin action)
        transaction = Transaction(
            word_id=word.id,
            buyer_name=owner_name or "ADMIN_RESET",
            price_paid=new_price,
            is_admin_action=True  # Mark as admin action - won't count in revenue
        )
        db.add(transaction)

        db.commit()
        db.refresh(word)

        return word

    @staticmethod
    def get_dashboard_summary(db: Session) -> dict:
        """
        Get comprehensive dashboard summary.

        Returns:
            Dictionary with income stats, popular words, recent errors
        """
        income_stats = AdminService.get_income_stats(db)
        popular_words = AdminService.get_most_viewed_words(db, limit=20)
        recent_errors = AdminService.get_recent_errors(db, limit=50)

        # Additional stats
        total_words = db.query(Word).count()
        available_words = db.query(Word).filter(
            or_(
                Word.lockout_ends_at == None,
                Word.lockout_ends_at < datetime.now(timezone.utc)
            )
        ).count()

        return {
            "income": income_stats,
            "popular_words": popular_words,
            "recent_errors": recent_errors,
            "stats": {
                "total_words": total_words,
                "available_words": available_words,
                "locked_words": total_words - available_words
            }
        }

    @staticmethod
    def report_message(db: Session, word_id: int, ip_address: Optional[str] = None) -> int:
        """
        Report a message as offensive.

        Args:
            db: Database session
            word_id: ID of word with offensive message
            ip_address: Reporter's IP address (optional)

        Returns:
            Current report count for the word
        """
        # Create report
        report = MessageReport(word_id=word_id, ip_address=ip_address)
        db.add(report)
        db.commit()

        # Get current report count
        report_count = db.query(MessageReport).filter(MessageReport.word_id == word_id).count()

        # Auto-moderate if threshold reached and not already moderated
        word = db.query(Word).filter(Word.id == word_id).first()
        if word and report_count >= settings.report_threshold and not word.moderation_status:
            word.moderation_status = "pending"
            db.commit()

        return report_count

    @staticmethod
    def get_reported_messages(db: Session, page: int = 1, page_size: int = 20) -> dict:
        """
        Get all messages that have been reported and are still current.
        Only shows messages that are still active on the word (not replaced by new owner).

        Args:
            db: Database session
            page: Page number (1-indexed)
            page_size: Number of results per page

        Returns:
            Dictionary with reported messages, pagination info
        """
        # Get words with reports where the message is still current
        # (has reports and owner_message is not None)
        query = db.query(
            Word.id,
            Word.text,
            Word.owner_name,
            Word.owner_message,
            Word.moderation_status,
            Word.moderated_at,
            Word.updated_at,
            Word.lockout_ends_at,
            func.count(MessageReport.id).label('report_count')
        )\
            .join(MessageReport, Word.id == MessageReport.word_id)\
            .filter(Word.owner_message.isnot(None))\
            .group_by(
                Word.id,
                Word.text,
                Word.owner_name,
                Word.owner_message,
                Word.moderation_status,
                Word.moderated_at,
                Word.updated_at,
                Word.lockout_ends_at
            )\
            .having(func.count(MessageReport.id) >= 1)\
            .order_by(func.count(MessageReport.id).desc())

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        results = query.offset(offset).limit(page_size).all()

        return {
            "messages": [
                {
                    "word_id": row.id,
                    "word_text": row.text,
                    "owner_name": row.owner_name,
                    "owner_message": row.owner_message,
                    "report_count": row.report_count,
                    "moderation_status": row.moderation_status,
                    "moderated_at": row.moderated_at.isoformat() if row.moderated_at else None,
                    "updated_at": row.updated_at.isoformat(),
                    "lockout_ends_at": row.lockout_ends_at.isoformat() if row.lockout_ends_at else None
                }
                for row in results
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    @staticmethod
    def moderate_message(db: Session, word_id: int, action: str) -> Word:
        """
        Moderate a reported message.

        Args:
            db: Database session
            word_id: ID of word to moderate
            action: "approve", "reject", or "protect"

        Returns:
            Updated Word instance

        Raises:
            ValueError: If word not found or invalid action
        """
        word = db.query(Word).filter(Word.id == word_id).first()

        if not word:
            raise ValueError(f"Word with ID {word_id} not found")

        if action not in ["approve", "reject", "protect"]:
            raise ValueError(f"Invalid action: {action}")

        if action == "protect":
            # Protected messages cannot be reported/flagged
            word.moderation_status = "protected"
            word.moderated_at = datetime.now(timezone.utc)

            # Reset countdown timer if word is currently locked
            if word.lockout_ends_at and word.lockout_ends_at > datetime.now(timezone.utc):
                # Calculate lockout based on the price paid (current price - 1)
                price_paid = float(word.price) - 1
                lockout_hours = price_paid  # 1 hour per dollar paid
                word.lockout_ends_at = datetime.now(timezone.utc) + timedelta(hours=lockout_hours)

            # Clear all reports for this word since it's now protected
            db.query(MessageReport).filter(MessageReport.word_id == word_id).delete()
        else:
            word.moderation_status = "approved" if action == "approve" else "rejected"
            word.moderated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(word)

        return word

    @staticmethod
    def get_report_count(db: Session, word_id: int) -> int:
        """
        Get the number of reports for a specific word.

        Args:
            db: Database session
            word_id: ID of word

        Returns:
            Report count
        """
        return db.query(MessageReport).filter(MessageReport.word_id == word_id).count()
