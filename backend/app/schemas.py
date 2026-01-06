"""
Pydantic schemas for request/response validation
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, UUID4
from enum import Enum


# Enums
class PlatformType(str, Enum):
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    INSTAGRAM = "instagram"


class MessageStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"



# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True


# User schemas
class UserBase(BaseSchema):
    email: EmailStr
    business_name: str
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(BaseSchema):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: UUID4
    business_name: str
    phone_number: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    # Telegram Bot
    telegram_bot_token: Optional[str] = None
    telegram_bot_username: Optional[str] = None
    business_context: Optional[str] = None
    
    is_active: bool
    is_verified: bool
    created_at: datetime


class UserUpdate(BaseSchema):
    business_name: Optional[str] = None
    phone_number: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    # Telegram Bot
    telegram_bot_token: Optional[str] = None
    telegram_bot_username: Optional[str] = None
    
    business_context: Optional[str] = None


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# Customer schemas
class CustomerBase(BaseSchema):
    name: str
    phone_number: str
    email: Optional[EmailStr] = None
    business_info: Optional[str] = None
    tags: List[str] = []


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseSchema):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    business_info: Optional[str] = None
    tags: Optional[List[str]] = None


class CustomerResponse(CustomerBase):
    id: UUID4
    user_id: UUID4
    first_contact_date: datetime
    last_contact_date: datetime
    total_orders: int
    total_spent: float
    is_active: bool
    created_at: datetime


# Message schemas
class MessageBase(BaseSchema):
    content: str


class MessageCreate(MessageBase):
    conversation_id: UUID4
    is_from_customer: bool


class MessageSend(BaseSchema):
    customer_id: UUID4
    platform: PlatformType
    content: str


class MessageResponse(MessageBase):
    id: UUID4
    conversation_id: UUID4
    is_from_customer: bool
    status: MessageStatus
    ai_generated: bool
    intent_detected: Optional[str] = None
    sentiment: Optional[str] = None
    created_at: datetime


# Conversation schemas
class ConversationBase(BaseSchema):
    platform: PlatformType


class ConversationResponse(ConversationBase):
    id: UUID4
    customer_id: UUID4
    customer_name: Optional[str] = None
    is_active: bool
    last_message_at: datetime
    created_at: datetime


class ConversationWithMessages(ConversationResponse):
    messages: List[MessageResponse] = []
    customer: CustomerResponse


# Order schemas
class OrderItem(BaseSchema):
    name: str
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)


class OrderBase(BaseSchema):
    items: List[OrderItem]
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    customer_id: UUID4


class OrderUpdate(BaseSchema):
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None


class OrderResponse(BaseSchema):
    id: UUID4
    user_id: UUID4
    customer_id: UUID4
    customer_name: Optional[str] = None  # Added field
    order_number: str
    items: List[Dict[str, Any]]
    total_amount: float
    currency: str
    status: OrderStatus
    notes: Optional[str] = None
    receipt_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


# Follow-up schemas
class FollowUpBase(BaseSchema):
    message: str
    scheduled_for: datetime
    reason: Optional[str] = None


class FollowUpCreate(FollowUpBase):
    customer_id: UUID4


class FollowUpResponse(FollowUpBase):
    id: UUID4
    customer_id: UUID4
    is_sent: bool
    sent_at: Optional[datetime] = None
    created_at: datetime


# Analytics schemas
class AnalyticsOverview(BaseSchema):
    total_customers: int
    active_conversations: int
    total_orders: int
    total_revenue: float
    average_response_time: float  # in seconds
    leads_this_week: int
    customers_needing_attention: int


class ResponseTimeMetrics(BaseSchema):
    average_response_time: float
    median_response_time: float
    fastest_response: float
    slowest_response: float


class LeadStatistics(BaseSchema):
    total_leads: int
    converted_leads: int
    conversion_rate: float
    leads_by_platform: Dict[str, int]


# Webhook schemas
class TwilioWebhook(BaseSchema):
    MessageSid: str
    From: str
    To: str
    Body: str
    NumMedia: Optional[str] = "0"

