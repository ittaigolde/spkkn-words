from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timezone

from ..database import get_db
from ..models import Word, Transaction
from ..schemas import WordResponse, TransactionResponse
from ..utils import is_word_available

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("/expensive", response_model=list[WordResponse])
async def get_most_expensive(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get the most expensive words.

    Returns the top N words by current price, regardless of availability.

    Args:
        limit: Maximum number of words to return (default: 10)
    """
    words = db.query(Word).order_by(desc(Word.price)).limit(limit).all()

    return [
        WordResponse(
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
        for word in words
    ]


@router.get("/recent", response_model=list[TransactionResponse])
async def get_recent_purchases(
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
async def get_platform_stats(db: Session = Depends(get_db)):
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
