from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from .models import Word, Transaction
from .utils import is_word_available


class WordService:
    """Service layer for word business logic."""

    @staticmethod
    def steal_word(
        word_text: str,
        owner_name: str,
        owner_message: str,
        db: Session
    ) -> tuple[Word, Transaction]:
        """
        Purchase a word (the "steal" mechanic).

        This function handles:
        1. Checking if word is available
        2. Calculating new price (+$1 from current price)
        3. Calculating lockout duration (1 hour per $1 spent)
        4. Updating word ownership
        5. Creating transaction record

        Uses database transaction with row-level locking to prevent race conditions.

        Args:
            word_text: The word to purchase
            owner_name: Name of the purchaser
            owner_message: Custom message (max 140 chars)
            db: Database session

        Returns:
            Tuple of (updated_word, transaction)

        Raises:
            HTTPException: If word not found, not available, or validation fails
        """
        try:
            # Lock the row for update to prevent race conditions
            word = db.query(Word).filter(
                Word.text == word_text.lower()
            ).with_for_update().first()

            if not word:
                raise HTTPException(status_code=404, detail="Word not found")

            # Check if word is available
            if not is_word_available(word.lockout_ends_at):
                time_remaining = word.lockout_ends_at - datetime.now(timezone.utc)
                hours = int(time_remaining.total_seconds() // 3600)
                minutes = int((time_remaining.total_seconds() % 3600) // 60)
                raise HTTPException(
                    status_code=400,
                    detail=f"Word is currently locked. Time remaining: {hours}h {minutes}m"
                )

            # Calculate purchase price (current price of the word)
            purchase_price = word.price

            # Calculate new price (increases by $1.00)
            new_price = purchase_price + Decimal("1.00")

            # Calculate lockout duration (1 hour per $1.00 spent)
            lockout_hours = float(purchase_price)
            lockout_duration = timedelta(hours=lockout_hours)
            lockout_ends_at = datetime.now(timezone.utc) + lockout_duration

            # Update word ownership
            word.owner_name = owner_name
            word.owner_message = owner_message
            word.price = new_price
            word.lockout_ends_at = lockout_ends_at

            # Create transaction record
            transaction = Transaction(
                word_id=word.id,
                buyer_name=owner_name,
                price_paid=purchase_price
            )
            db.add(transaction)

            # Commit the transaction
            db.commit()
            db.refresh(word)
            db.refresh(transaction)

            return word, transaction

        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(e)}"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(e)}"
            )

    @staticmethod
    def validate_content(text: str) -> tuple[bool, str]:
        """
        Validate user-generated content (owner_message).

        Checks for:
        - Profanity (basic check)
        - URLs and external links
        - Email addresses
        - Phone numbers
        - Social media handles

        Returns:
            Tuple of (is_valid, error_message)
        """
        import re

        # Check for URLs
        url_pattern = r'https?://|www\.|\.com|\.net|\.org|\.io|\.ai'
        if re.search(url_pattern, text, re.IGNORECASE):
            return False, "URLs and web links are not allowed"

        # Check for email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, text):
            return False, "Email addresses are not allowed"

        # Check for social media handles
        handle_pattern = r'@\w+'
        if re.search(handle_pattern, text):
            return False, "Social media handles are not allowed"

        # Check for phone numbers (basic)
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        if re.search(phone_pattern, text):
            return False, "Phone numbers are not allowed"

        # Basic profanity check (extend this list as needed)
        profanity_list = ['fuck', 'shit', 'bitch', 'asshole', 'damn']
        text_lower = text.lower()
        for word in profanity_list:
            if word in text_lower:
                return False, "Profanity is not allowed"

        return True, ""
