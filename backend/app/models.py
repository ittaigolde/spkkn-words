from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class Word(Base):
    """Word model representing each word in the registry."""
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(100), unique=True, nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False, default=1.00)
    owner_name = Column(String(100), nullable=True)
    owner_message = Column(String(140), nullable=True)
    lockout_ends_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    transactions = relationship("Transaction", back_populates="word")

    # Indexes
    __table_args__ = (
        Index('idx_words_price', 'price'),
        Index('idx_words_lockout_ends_at', 'lockout_ends_at'),
    )


class Transaction(Base):
    """Transaction model - immutable log of all word purchases."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    buyer_name = Column(String(100), nullable=False)
    price_paid = Column(Numeric(10, 2), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    word = relationship("Word", back_populates="transactions")

    # Indexes
    __table_args__ = (
        Index('idx_transactions_word_id', 'word_id'),
        Index('idx_transactions_timestamp', 'timestamp'),
    )
