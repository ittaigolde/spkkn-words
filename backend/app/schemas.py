from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal


class WordBase(BaseModel):
    """Base word schema."""
    text: str
    price: Decimal
    owner_name: Optional[str] = None
    owner_message: Optional[str] = None
    lockout_ends_at: Optional[datetime] = None


class WordResponse(WordBase):
    """Word response with computed fields."""
    id: int
    is_available: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WordDetailResponse(WordResponse):
    """Detailed word response including transaction history."""
    transaction_count: int
    transactions: list["TransactionResponse"] = []


class TransactionResponse(BaseModel):
    """Transaction response schema."""
    id: int
    buyer_name: str
    price_paid: Decimal
    timestamp: datetime

    class Config:
        from_attributes = True


class WordSearchResponse(BaseModel):
    """Search results response."""
    words: list[WordResponse]
    total: int
    page: int
    page_size: int


class PurchaseRequest(BaseModel):
    """Request to purchase a word."""
    owner_name: str = Field(..., min_length=1, max_length=100)
    owner_message: str = Field(..., min_length=1, max_length=140)


class PurchaseResponse(BaseModel):
    """Response after purchasing a word."""
    success: bool
    word: WordResponse
    transaction_id: int
    message: str


class ConfirmPurchaseRequest(BaseModel):
    """Request to confirm purchase after payment."""
    payment_intent_id: str
    word_text: str
    owner_name: str
    owner_message: str
    is_new_word: bool
