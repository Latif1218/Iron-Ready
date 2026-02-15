from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from datetime import datetime

from ..database import Base

class TransactionType(str, PyEnum):
    """Possible types of financial transactions"""
    SUBSCRIPTION_PAYMENT = "subscription_payment"     
    SUBSCRIPTION_RENEWAL = "subscription_renewal"     
    REFUND = "refund"                                 
    WITHDRAWAL = "withdrawal"                     
    ADJUSTMENT = "adjustment"                         
    OTHER = "other"


class TransactionStatus(str, PyEnum):
    """Current status of the transaction"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    stripe_payment_intent_id = Column(String(100), nullable=True, unique=True, index=True)
    stripe_charge_id = Column(String(100), nullable=True, index=True)
    stripe_payout_id = Column(String(100), nullable=True, index=True) 
    type = Column(Enum(TransactionType), nullable=False, index=True)
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING, index=True)
    amount = Column(Float(precision=2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    payment_method = Column(String(50), nullable=True) 
    description = Column(String(255), nullable=True)
    subscription_id = Column(String(100), ForeignKey("subscriptions.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    
    user = relationship("User", back_populates="transactions", foreign_keys=[user_id])
    subscription = relationship("Subscription", back_populates="transactions")

    def __repr__(self):
        sign = "+" if self.amount > 0 else "-"
        return f"<Transaction #{self.id} | {self.type} | {sign}${abs(self.amount):.2f} | {self.status}>"