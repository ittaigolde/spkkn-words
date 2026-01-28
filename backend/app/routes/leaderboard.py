from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timezone
from fastapi_cache.decorator import cache

from ..database import get_db
from ..models import Word, Transaction, MessageReport
from ..schemas import WordResponse, TransactionResponse
from ..utils import is_word_available
from ..cache import CACHE_TTL_LEADERBOARD, CACHE_TTL_STATS
from ..ratelimit import limiter
from ..rate_config import RateLimits
from ..services import filter_message_for_moderation

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("/expensive", response_model=list[WordResponse])
@limiter.limit(RateLimits.LEADERBOARD)
@cache(expire=CACHE_TTL_LEADERBOARD)
async def get_most_expensive(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get the most expensive words that have been purchased.

    Returns the top N words by current price that have owners.

    Args:
        limit: Maximum number of words to return (default: 10)
    """
    # Only get words that have been bought (price > $1.00)
    # Words start at $1.00, after first purchase they become $2.00
    words = db.query(Word).filter(
        Word.price > 1.00
    ).order_by(desc(Word.price)).limit(limit).all()

    result = []
    for word in words:
        # Get report count
        report_count = db.query(MessageReport).filter(MessageReport.word_id == word.id).count()

        # Filter message based on moderation status
        filtered_message = filter_message_for_moderation(
            word.owner_message,
            word.moderation_status,
            report_count
        )

        result.append(WordResponse(
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
        ))

    return result


@router.get("/recent", response_model=list[TransactionResponse])
@limiter.limit(RateLimits.LEADERBOARD)
@cache(expire=CACHE_TTL_LEADERBOARD)
async def get_recent_purchases(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get recently purchased words.

    Returns the most recent N transactions.

    Args:
        limit: Maximum number of transactions to return (default: 10)
    """
    transactions = db.query(Transaction).order_by(
        desc(Transaction.timestamp)
    ).limit(limit).all()

    return [
        TransactionResponse(
            id=t.id,
            buyer_name=t.buyer_name,
            price_paid=t.price_paid,
            timestamp=t.timestamp
        )
        for t in transactions
    ]


@router.get("/stats")
@limiter.limit(RateLimits.LEADERBOARD)
@cache(expire=CACHE_TTL_STATS)
async def get_platform_stats(request: Request, db: Session = Depends(get_db)):
    """
    Get platform-wide statistics.

    Returns:
        - total_words: Total number of words in database
        - words_owned: Number of words currently locked
        - words_available: Number of words available for purchase
        - total_transactions: Total number of purchases
        - total_revenue: Total platform revenue
        - average_price: Average word price
    """
    now = datetime.now(timezone.utc)

    # Total words
    total_words = db.query(func.count(Word.id)).scalar()

    # Words currently locked
    words_owned = db.query(func.count(Word.id)).filter(
        Word.lockout_ends_at.isnot(None),
        Word.lockout_ends_at > now
    ).scalar()

    # Words available
    words_available = total_words - words_owned

    # Total transactions
    total_transactions = db.query(func.count(Transaction.id)).scalar()

    # Total revenue (sum of all transaction amounts)
    total_revenue = db.query(func.sum(Transaction.price_paid)).scalar() or 0

    # Average price
    average_price = db.query(func.avg(Word.price)).scalar() or 0

    return {
        "total_words": total_words,
        "words_owned": words_owned,
        "words_available": words_available,
        "total_transactions": total_transactions,
        "total_revenue": float(total_revenue),
        "average_price": float(average_price)
    }
