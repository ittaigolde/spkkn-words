from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import PurchaseRequest, PurchaseResponse, WordResponse
from ..services import WordService
from ..utils import is_word_available
from ..ratelimit import limiter
from ..rate_config import RateLimits

router = APIRouter(prefix="/api/purchase", tags=["purchase"])


@router.post("/{word_text}", response_model=PurchaseResponse)
@limiter.limit(RateLimits.PURCHASE_WORD)
async def purchase_word(
    word_text: str,
    request: Request,
    purchase_data: PurchaseRequest,
    db: Session = Depends(get_db)
):
    """
    Purchase a word (the "steal" mechanic).

    This endpoint:
    1. Validates the owner_name and owner_message
    2. Checks if the word is available
    3. Processes the purchase (increases price by $1, sets lockout)
    4. Creates a transaction record

    Note: This is the pre-payment endpoint. In production, this would be
    called after successful Stripe payment.

    Args:
        word_text: The word to purchase
        purchase_data: Purchase details (owner_name, owner_message)

    Returns:
        Purchase confirmation with updated word details
    """
    # Validate content
    is_valid, error_msg = WordService.validate_content(purchase_data.owner_message)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    is_valid, error_msg = WordService.validate_content(purchase_data.owner_name)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Process the purchase
    word, transaction = WordService.steal_word(
        word_text=word_text,
        owner_name=purchase_data.owner_name,
        owner_message=purchase_data.owner_message,
        db=db
    )

    word_response = WordResponse(
        id=word.id,
        text=word.text,
        price=word.price,
        owner_name=word.owner_name,
        owner_message=word.owner_message,
        lockout_ends_at=word.lockout_ends_at,
        is_available=is_word_available(word.lockout_ends_at),
        created_at=word.created_at,
        updated_at=word.updated_at
    )

    return PurchaseResponse(
        success=True,
        word=word_response,
        transaction_id=transaction.id,
        message=f"Successfully purchased '{word_text}' for ${transaction.price_paid}!"
    )


@router.post("/add/{word_text}", response_model=PurchaseResponse)
@limiter.limit(RateLimits.ADD_WORD)
async def add_word(
    word_text: str,
    request: Request,
    purchase_data: PurchaseRequest,
    db: Session = Depends(get_db)
):
    """
    Add a new word to the registry for $50.

    This endpoint:
    1. Validates the word doesn't already exist
    2. Validates the owner_name and owner_message
    3. Creates the word with 50-hour lockout
    4. Sets next purchase price to $51
    5. Creates a transaction record

    Note: This is the pre-payment endpoint. In production, this would be
    called after successful Stripe payment.

    Args:
        word_text: The word to add
        purchase_data: Owner details (owner_name, owner_message)

    Returns:
        Confirmation with word details
    """
    # Validate content
    is_valid, error_msg = WordService.validate_content(purchase_data.owner_message)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    is_valid, error_msg = WordService.validate_content(purchase_data.owner_name)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Add the word
    word, transaction = WordService.add_word(
        word_text=word_text,
        owner_name=purchase_data.owner_name,
        owner_message=purchase_data.owner_message,
        db=db
    )

    word_response = WordResponse(
        id=word.id,
        text=word.text,
        price=word.price,
        owner_name=word.owner_name,
        owner_message=word.owner_message,
        lockout_ends_at=word.lockout_ends_at,
        is_available=is_word_available(word.lockout_ends_at),
        created_at=word.created_at,
        updated_at=word.updated_at
    )

    return PurchaseResponse(
        success=True,
        word=word_response,
        transaction_id=transaction.id,
        message=f"Successfully added '{word_text}' to the registry for $50!"
    )
