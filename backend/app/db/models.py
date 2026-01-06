"""
Database Models for KioskAI
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, 
    ForeignKey, Enum, Float, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
import uuid

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type for PostgreSQL,
    and CHAR(36) for SQLite.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return str(value)
        if not isinstance(value, uuid.UUID):
            return "%.32x" % uuid.UUID(value).int
        return "%.32x" % value.int
        # return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return value
import enum

from app.db.database import Base


class PlatformType(str, enum.Enum):
    """Message platform types"""
    TELEGRAM = "telegram"


class MessageStatus(str, enum.Enum):
    """Message delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class OrderStatus(str, enum.Enum):
    """Order status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"



class User(Base):
    """Business owner/user accounts"""
    __tablename__ = "users"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    business_name = Column(String(255), nullable=False)
    phone_number = Column(String(20))
    
    # Bank Details
    bank_name = Column(String(100))
    account_number = Column(String(50))
    account_name = Column(String(100))
    
    # Telegram Bot Configuration
    telegram_bot_token = Column(String(200))  # From @BotFather
    telegram_bot_username = Column(String(100))  # Bot's @username
    
    # AI Context
    business_context = Column(Text, nullable=True) # For products, prices, return policy
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customers = relationship("Customer", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")


class Customer(Base):
    """Customer profiles"""
    __tablename__ = "customers"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    
    # Basic info
    name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False, index=True)
    email = Column(String(255))
    
    # Business context
    business_info = Column(Text)  # What they do, their needs
    tags = Column(JSON, default=list)  # ["vip", "wholesale", etc.]
    
    # Engagement tracking
    first_contact_date = Column(DateTime, default=datetime.utcnow)
    last_contact_date = Column(DateTime, default=datetime.utcnow)
    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    
    # Metadata
    customer_metadata = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved by SQLAlchemy)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="customers")
    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    follow_ups = relationship("FollowUp", back_populates="customer", cascade="all, delete-orphan")


class Conversation(Base):
    """Chat sessions with customers"""
    __tablename__ = "conversations"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    customer_id = Column(GUID(), ForeignKey("customers.id"), nullable=False)
    
    platform = Column(Enum(PlatformType), nullable=False)
    platform_conversation_id = Column(String(255), index=True)  # External ID (removed global unique constraint for multi-tenancy)
    
    is_active = Column(Boolean, default=True)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    memories = relationship("ConversationMemory", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Individual messages"""
    __tablename__ = "messages"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(GUID(), ForeignKey("conversations.id"), nullable=False)
    
    # Message content
    content = Column(Text, nullable=False)
    is_from_customer = Column(Boolean, nullable=False)  # True if customer sent, False if AI sent
    
    # Status tracking
    status = Column(Enum(MessageStatus), default=MessageStatus.PENDING)
    platform_message_id = Column(String(255), index=True)  # External message ID
    
    # AI metadata
    ai_generated = Column(Boolean, default=False)
    intent_detected = Column(String(100))  # "inquiry", "order", "complaint", etc.
    sentiment = Column(String(50))  # "positive", "neutral", "negative"
    
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class Order(Base):
    """Customer orders"""
    __tablename__ = "orders"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    customer_id = Column(GUID(), ForeignKey("customers.id"), nullable=False)
    
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Order details
    items = Column(JSON, nullable=False)  # [{"name": "Product", "qty": 2, "price": 100}]
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="NGN")
    
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    notes = Column(Text)
    receipt_url = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")


class FollowUp(Base):
    """Scheduled follow-up reminders"""
    __tablename__ = "follow_ups"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    customer_id = Column(GUID(), ForeignKey("customers.id"), nullable=False)
    
    # Follow-up details
    message = Column(Text, nullable=False)
    scheduled_for = Column(DateTime, nullable=False)
    
    # Execution tracking
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    
    # Context
    reason = Column(String(100))  # "inactive", "unpaid_invoice", "order_reminder"
    followup_metadata = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="follow_ups")


class Review(Base):
    """Customer reviews and feedback"""
    __tablename__ = "reviews"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    
    # Review details
    customer_name = Column(String(200), nullable=False)
    review_text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    source = Column(String(50), default="manual")  # manual, google, facebook, etc.
    
    # Sentiment analysis
    sentiment = Column(String(50))  # positive, neutral, negative
    sentiment_score = Column(Float)  # 0.0 to 1.0
    urgency = Column(String(20))  # low, medium, high
    
    # AI response
    ai_response = Column(Text)
    response_approved = Column(Boolean, default=False)
    response_sent_at = Column(DateTime)
    
    # Triggers
    has_refund_request = Column(Boolean, default=False)
    has_complaint = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationMemory(Base):
    """Store conversation context for AI"""
    __tablename__ = "conversation_memories"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(GUID(), ForeignKey("conversations.id"), nullable=False)
    
    # Memory content
    summary = Column(Text, nullable=False)  # Summary of conversation segment
    key_points = Column(JSON, default=list)  # Important extracted points
    
    # Vector embedding for semantic search (requires pgvector extension)
    # embedding = Column(Vector(1536))  # Will add after pgvector setup
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="memories")
