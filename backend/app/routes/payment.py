"""
Stripe payment integration routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Header, Query
from sqlalchemy.orm import Session
import stripe
from typing import Optional
import hmac
import hashlib

from ..database import get_db
from ..config import get_settings
from ..schemas import PurchaseRequest, ConfirmPurchaseRequest
from ..services import WordService
from ..utils import is_word_available
from ..models import Word
from ..ratelimit import limiter
from ..rate_config import RateLimits

settings = get_settings()
stripe.api_key = settings.stripe_secret_key

router = APIRouter(prefix="/api/payment", tags=["payment"])


@router.post("/create-intent")
@limiter.limit(RateLimits.PURCHASE_WORD)
async def create_payment_intent(
    request: Request,
    word_text: str = Query(...),
    is_new_word: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe PaymentIntent for a word purchase.

    Args:
        word_text: The word to purchase
        is_new_word: True if adding a new word ($50), False for existing word

    Returns:
        client_secret: For completing payment on frontend
        amount: Amount in cents
        word_data: Current word information
    """
    try:
        print(f"Creating payment intent - word: {word_text}, is_new_word: {is_new_word}")
        if is_new_word:
            # Check if word already exists
            existing = db.query(Word).filter(Word.text == word_text.lower()).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Word already exists in registry"
                )

            amount = 5000  # $50.00 in cents
            description = f"Add word '{word_text}' to The Word Registry"
        else:
            # Get existing word
            word = db.query(Word).filter(Word.text == word_text.lower()).first()
            if not word:
                raise HTTPException(status_code=404, detail="Word not found")

            # Check availability
            if not is_word_available(word.lockout_ends_at):
                raise HTTPException(
                    status_code=400,
                    detail="Word is currently locked"
                )

            amount = int(float(word.price) * 100)  # Convert to cents
            description = f"Purchase word '{word_text}' from The Word Registry"

        # Create statement descriptor for credit card statement
        # Format: "WORD* LOVE" (max 22 chars, limited character set)
        word_upper = word_text.upper()[:16]  # Leave room for "WORD* "
        statement_descriptor = f"WORD* {word_upper}"

        # Create PaymentIntent
        print(f"DEBUG: stripe.api_key starts with: {stripe.api_key[:10] if stripe.api_key else 'NOT SET'}...")
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            description=description,
            statement_descriptor=statement_descriptor,
            metadata={
                "word": word_text,
                "is_new_word": str(is_new_word)
            },
            # Use automatic payment methods
            automatic_payment_methods={
                "enabled": True,
            },
        )

        return {
            "client_secret": payment_intent.client_secret,
            "amount": amount,
            "word": word_text,
            "is_new_word": is_new_word
        }

    except stripe.error.StripeError as e:
        print(f"Stripe error creating payment intent: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/confirm-purchase")
async def confirm_purchase(
    request_data: ConfirmPurchaseRequest,
    db: Session = Depends(get_db)
):
    """
    Confirm purchase after successful payment.
    Called from frontend after payment is confirmed.
    """
    try:
        print(f"Confirming purchase - payment_intent_id: {request_data.payment_intent_id}, word: {request_data.word_text}")
        # Verify payment was successful
        payment_intent = stripe.PaymentIntent.retrieve(request_data.payment_intent_id)

        if payment_intent.status != "succeeded":
            raise HTTPException(
                status_code=400,
                detail="Payment not completed"
            )

        # Validate content
        is_valid, error_msg = WordService.validate_content(request_data.owner_message)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        is_valid, error_msg = WordService.validate_content(request_data.owner_name)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Process the purchase
        if request_data.is_new_word:
            word, transaction = WordService.add_word(
                word_text=request_data.word_text,
                owner_name=request_data.owner_name,
                owner_message=request_data.owner_message,
                db=db
            )
        else:
            word, transaction = WordService.steal_word(
                word_text=request_data.word_text,
                owner_name=request_data.owner_name,
                owner_message=request_data.owner_message,
                db=db
            )

        return {
            "success": True,
            "word": word.text,
            "transaction_id": transaction.id,
            "message": "Purchase completed successfully!"
        }

    except stripe.error.StripeError as e:
        print(f"Stripe error confirming purchase: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.

    This endpoint receives notifications from Stripe about payment events.
    """
    payload = await request.body()

    # For testing without webhook secret
    if not settings.stripe_webhook_secret:
        return {"status": "webhook received (no verification)"}

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )

        # Handle different event types
        if event.type == "payment_intent.succeeded":
            payment_intent = event.data.object
            print(f"Payment succeeded: {payment_intent.id}")
            # Additional processing if needed

        elif event.type == "payment_intent.payment_failed":
            payment_intent = event.data.object
            print(f"Payment failed: {payment_intent.id}")
            # Handle failed payment

        return {"status": "success"}

    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")
