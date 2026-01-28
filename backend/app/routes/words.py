from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from ..database import get_db
from ..models import Word, Transaction, MessageReport
from ..schemas import WordResponse, WordDetailResponse, WordSearchResponse, TransactionResponse, ReportResponse
from ..utils import is_word_available
from ..ratelimit import limiter
from ..rate_config import RateLimits
from ..services import WordService, filter_message_for_moderation
from ..admin_service import AdminService

router = APIRouter(prefix="/api/words", tags=["words"])


class ValidateContentRequest(BaseModel):
    owner_name: str
    owner_message: str


@router.get("/search", response_model=WordSearchResponse)
@limiter.limit(RateLimits.WORD_SEARCH)
async def search_words(
    request: Request,
    q: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query(None, description="Filter by status: available, locked, all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search for words.

    - **q**: Search query (searches word text)
    - **status**: Filter by availability (available, locked, all)
    - **page**: Page number
    - **page_size**: Results per page
    """
    query = db.query(Word)

    # Apply search filter
    if q:
        query = query.filter(Word.text.ilike(f"%{q}%"))

    # Apply status filter
    now = datetime.now(timezone.utc)
    if status == "available":
        query = query.filter(
            or_(
                Word.lockout_ends_at.is_(None),
                Word.lockout_ends_at <= now
            )
        )
    elif status == "locked":
        query = query.filter(
            Word.lockout_ends_at.isnot(None),
            Word.lockout_ends_at > now
        )

    # Get total count
    total = query.count()

    # Apply pagination
    words = query.order_by(Word.text).offset((page - 1) * page_size).limit(page_size).all()

    # Add is_available field and filter messages
    word_responses = []
    for word in words:
        # Get report count
        report_count = db.query(MessageReport).filter(MessageReport.word_id == word.id).count()

        # Filter message based on moderation status
        filtered_message = filter_message_for_moderation(
            word.owner_message,
            word.moderation_status,
            report_count
        )

        word_dict = {
            "id": word.id,
            "text": word.text,
            "price": word.price,
            "owner_name": word.owner_name,
            "owner_message": filtered_message,
            "lockout_ends_at": word.lockout_ends_at,
            "is_available": is_word_available(word.lockout_ends_at),
            "created_at": word.created_at,
            "updated_at": word.updated_at,
            "moderation_status": word.moderation_status,
            "report_count": report_count
        }
        word_responses.append(WordResponse(**word_dict))

    return WordSearchResponse(
        words=word_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/random", response_model=WordResponse)
@limiter.limit(RateLimits.RANDOM_WORD)
async def get_random_word(
    request: Request,
    available_only: bool = Query(True, description="Only return available words"),
    base_price_only: bool = Query(True, description="Only return $1 words"),
    db: Session = Depends(get_db)
):
    """
    Get a random word.

    - **available_only**: Only return words that can be purchased
    - **base_price_only**: Only return words at base price ($1.00)
    """
    query = db.query(Word)

    now = datetime.now(timezone.utc)

    if available_only:
        query = query.filter(
            or_(
                Word.lockout_ends_at.is_(None),
                Word.lockout_ends_at <= now
            )
        )

    if base_price_only:
        query = query.filter(Word.price == 1.00)

    # Get random word using PostgreSQL's RANDOM()
    word = query.order_by(func.random()).first()

    if not word:
        raise HTTPException(status_code=404, detail="No words found matching criteria")

    # Get report count
    report_count = db.query(MessageReport).filter(MessageReport.word_id == word.id).count()

    # Filter message based on moderation status
    filtered_message = filter_message_for_moderation(
        word.owner_message,
        word.moderation_status,
        report_count
    )

    return WordResponse(
        id=word.id,
        text=word.text,
        price=word.price,
        owner_name=word.owner_name,
        owner_message=filtered_message,
        lockout_ends_at=word.lockout_ends_at,
        is_available=is_word_available(word.lockout_ends_at),
        created_at=word.created_at,
        updated_at=word.updated_at,
        moderation_status=word.moderation_status,
        report_count=report_count
    )


@router.get("/{word_text}", response_model=WordDetailResponse)
@limiter.limit(RateLimits.WORD_DETAIL)
async def get_word(
    word_text: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific word.

    - **word_text**: The word to look up
    """
    word = db.query(Word).filter(Word.text == word_text.lower()).first()

    if not word:
        raise HTTPException(status_code=404, detail="Word not found")

    # Log word view for analytics (async, don't wait)
    try:
        from ..admin_service import AdminService
        ip_address = request.client.host if request.client else None
        AdminService.log_word_view(db, word.id, ip_address)
    except Exception:
        pass  # Don't fail request if view logging fails

    # Get transaction history (exclude admin actions from public view)
    transactions = db.query(Transaction).filter(
        Transaction.word_id == word.id,
        Transaction.is_admin_action == False  # Only show real purchases
    ).order_by(Transaction.timestamp.desc()).all()

    transaction_responses = [
        TransactionResponse(
            id=t.id,
            buyer_name=t.buyer_name,
            price_paid=t.price_paid,
            timestamp=t.timestamp
        )
        for t in transactions
    ]

    # Get report count
    report_count = db.query(MessageReport).filter(MessageReport.word_id == word.id).count()

    # Filter message based on moderation status
    filtered_message = filter_message_for_moderation(
        word.owner_message,
        word.moderation_status,
        report_count
    )

    return WordDetailResponse(
        id=word.id,
        text=word.text,
        price=word.price,
        owner_name=word.owner_name,
        owner_message=filtered_message,
        lockout_ends_at=word.lockout_ends_at,
        is_available=is_word_available(word.lockout_ends_at),
        created_at=word.created_at,
        updated_at=word.updated_at,
        moderation_status=word.moderation_status,
        report_count=report_count,
        transaction_count=len(transactions),
        transactions=transaction_responses
    )


@router.post("/validate-content")
@limiter.limit("30/minute")
async def validate_content(
    request: Request,
    content: ValidateContentRequest
):
    """
    Validate owner name and message for profanity and toxic content.
    This allows frontend to validate before payment processing.

    Returns:
        {"valid": true} if content is acceptable
        {"valid": false, "error": "reason"} if content is rejected
    """
    # Validate owner_name
    is_valid, error_msg = WordService.validate_content(content.owner_name)
    if not is_valid:
        return {
            "valid": False,
            "error": f"Name validation failed: {error_msg}"
        }

    # Validate owner_message
    is_valid, error_msg = WordService.validate_content(content.owner_message)
    if not is_valid:
        return {
            "valid": False,
            "error": f"Message validation failed: {error_msg}"
        }

    return {"valid": True}


@router.post("/{word_text}/report", response_model=ReportResponse)
@limiter.limit("5/day")
async def report_message(
    request: Request,
    word_text: str,
    db: Session = Depends(get_db)
):
    """
    Report a word's message as offensive.
    Limited to 5 reports per day per IP address (via rate limiter).

    Args:
        word_text: The word whose message to report

    Returns:
        Report confirmation with current report count
    """
    # Find the word
    word = db.query(Word).filter(func.lower(Word.text) == word_text.lower()).first()

    if not word:
        raise HTTPException(status_code=404, detail="Word not found")

    if not word.owner_message:
        raise HTTPException(status_code=400, detail="This word has no message to report")

    # Check if message is protected
    if word.moderation_status == "protected":
        raise HTTPException(status_code=400, detail="This message has been protected by moderators and cannot be reported")

    # Get client IP
    ip_address = request.client.host if request.client else None

    # Create report
    report_count = AdminService.report_message(db, word.id, ip_address)

    return ReportResponse(
        success=True,
        message="Report submitted successfully",
        report_count=report_count
    )
