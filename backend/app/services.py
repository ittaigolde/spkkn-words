from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from detoxify import Detoxify
from better_profanity import profanity

from .models import Word, Transaction
from .utils import is_word_available

# Initialize detoxify model (loads once)
_detoxify_model = None

def get_detoxify_model():
    """Lazy load the detoxify model to avoid loading it on import."""
    global _detoxify_model
    if _detoxify_model is None:
        _detoxify_model = Detoxify('original')
    return _detoxify_model


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
    def add_word(
        word_text: str,
        owner_name: str,
        owner_message: str,
        db: Session
    ) -> tuple[Word, Transaction]:
        """
        Add a new word to the registry for $50.

        This function handles:
        1. Checking if word already exists
        2. Creating new word with price $51 (after $50 purchase)
        3. Setting 50-hour lockout
        4. Creating transaction record with $50 paid

        Args:
            word_text: The word to add
            owner_name: Name of the creator/owner
            owner_message: Custom message (max 140 chars)
            db: Database session

        Returns:
            Tuple of (new_word, transaction)

        Raises:
            HTTPException: If word already exists or validation fails
        """
        try:
            word_text = word_text.lower().strip()

            # Check if word already exists
            existing_word = db.query(Word).filter(
                Word.text == word_text
            ).first()

            if existing_word:
                raise HTTPException(
                    status_code=400,
                    detail=f"Word '{word_text}' already exists in the registry"
                )

            # Validate word text (basic checks)
            if not word_text or len(word_text) > 100:
                raise HTTPException(
                    status_code=400,
                    detail="Word must be between 1 and 100 characters"
                )

            # Only allow English alphabetic characters (ASCII a-z)
            if not word_text.isalpha():
                raise HTTPException(
                    status_code=400,
                    detail="Word must contain only letters"
                )

            # Check for English-only (no foreign characters or emojis)
            if not word_text.isascii():
                raise HTTPException(
                    status_code=400,
                    detail="Word must contain only English letters (no foreign characters or emojis)"
                )

            # Check for toxicity/hate speech using detoxify
            try:
                model = get_detoxify_model()
                results = model.predict(word_text)

                # Check toxicity scores (threshold: 0.7)
                # Available scores: toxicity, severe_toxicity, obscene, threat, insult, identity_attack
                if results['toxicity'] > 0.7:
                    raise HTTPException(
                        status_code=400,
                        detail="This word contains inappropriate or toxic content"
                    )
                if results['identity_attack'] > 0.7 or results['threat'] > 0.7:
                    raise HTTPException(
                        status_code=400,
                        detail="This word contains hate speech or threatening content"
                    )
                if results['insult'] > 0.7 or results['obscene'] > 0.7:
                    raise HTTPException(
                        status_code=400,
                        detail="This word contains offensive content"
                    )
            except HTTPException:
                raise
            except Exception as e:
                # If detoxify fails, log but don't block (fail open)
                print(f"Warning: Detoxify check failed for '{word_text}': {e}")

            # Create new word
            # User pays $50, so next purchase price is $51
            creation_fee = Decimal("50.00")
            new_price = Decimal("51.00")
            lockout_hours = 50
            lockout_duration = timedelta(hours=lockout_hours)
            lockout_ends_at = datetime.now(timezone.utc) + lockout_duration

            new_word = Word(
                text=word_text,
                price=new_price,
                owner_name=owner_name,
                owner_message=owner_message,
                lockout_ends_at=lockout_ends_at
            )
            db.add(new_word)
            db.flush()  # Get the ID

            # Create transaction record
            transaction = Transaction(
                word_id=new_word.id,
                buyer_name=owner_name,
                price_paid=creation_fee
            )
            db.add(transaction)

            # Commit the transaction
            db.commit()
            db.refresh(new_word)
            db.refresh(transaction)

            return new_word, transaction

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

        # Check for profanity using better-profanity
        if profanity.contains_profanity(text):
            return False, "Profanity is not allowed"

        # Check for toxicity using detoxify (for messages)
        try:
            model = get_detoxify_model()
            results = model.predict(text)

            # Use stricter thresholds for user messages (0.8)
            if results['toxicity'] > 0.8:
                return False, "Content contains inappropriate or toxic language"
            if results['identity_attack'] > 0.8:
                return False, "Content contains hate speech or discriminatory language"
            if results['threat'] > 0.8:
                return False, "Content contains threatening language"
            if results['insult'] > 0.8 or results['severe_toxicity'] > 0.8:
                return False, "Content contains offensive or abusive language"
        except Exception as e:
            # If detoxify fails, log but don't block (fail open)
            print(f"Warning: Detoxify check failed for message: {e}")

        return True, ""
