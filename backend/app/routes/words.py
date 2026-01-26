from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional
from datetime import datetime, timezone

from ..database import get_db
from ..models import Word, Transaction
from ..schemas import WordResponse, WordDetailResponse, WordSearchResponse, TransactionResponse
from ..utils import is_word_available
from ..ratelimit import limiter
from ..rate_config import RateLimits

router = APIRouter(prefix="/api/words", tags=["words"])


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

    # Add is_available field
    word_responses = []
    for word in words:
        word_dict = {
            "id": word.id,
            "text": word.text,
            "price": word.price,
            "owner_name": word.owner_name,
            "owner_message": word.owner_message,
            "lockout_ends_at": word.lockout_ends_at,
            "is_available": is_word_available(word.lockout_ends_at),
            "created_at": word.created_at,
            "updated_at": word.updated_at
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

    return WordResponse(
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

    # Get transaction history
    transactions = db.query(Transaction).filter(
        Transaction.word_id == word.id
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

    return WordDetailResponse(
        id=word.id,
        text=word.text,
        price=word.price,
        owner_name=word.owner_name,
        owner_message=word.owner_message,
        lockout_ends_at=word.lockout_ends_at,
        is_available=is_word_available(word.lockout_ends_at),
        created_at=word.created_at,
        updated_at=word.updated_at,
        transaction_count=len(transactions),
        transactions=transaction_responses
    )
