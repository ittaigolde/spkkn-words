from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Index, Boolean, Text
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
    is_admin_action = Column(Boolean, default=False, nullable=False)  # True for admin overrides

    # Relationships
    word = relationship("Word", back_populates="transactions")

    # Indexes
    __table_args__ = (
        Index('idx_transactions_word_id', 'word_id'),
        Index('idx_transactions_timestamp', 'timestamp'),
        Index('idx_transactions_is_admin_action', 'is_admin_action'),
    )


class ErrorLog(Base):
    """Error log model - tracks application errors."""
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, index=True)
    error_type = Column(String(100), nullable=False)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    endpoint = Column(String(200), nullable=True)
    user_info = Column(String(200), nullable=True)  # IP or user agent
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_error_logs_timestamp', 'timestamp'),
        Index('idx_error_logs_error_type', 'error_type'),
    )


class WordView(Base):
    """Word view model - tracks word page views for analytics."""
    __tablename__ = "word_views"

    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible

    # Relationships
    word = relationship("Word")

    # Indexes
    __table_args__ = (
        Index('idx_word_views_word_id', 'word_id'),
        Index('idx_word_views_timestamp', 'timestamp'),
    )
