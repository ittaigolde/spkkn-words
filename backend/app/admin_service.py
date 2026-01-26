"""
Admin service for analytics, error logging, and word management.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
import traceback

from .models import Word, Transaction, ErrorLog, WordView
from .utils import is_word_available


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
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
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
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

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
            word.lockout_ends_at = datetime.utcnow() + timedelta(hours=lockout_hours)
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
                Word.lockout_ends_at < datetime.utcnow()
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
