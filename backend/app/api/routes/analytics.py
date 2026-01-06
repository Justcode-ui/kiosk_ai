"""
Analytics and Insights API Routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import (
    User, Customer, Conversation, Message, Order,
    OrderStatus
)
from app.schemas import AnalyticsOverview, ResponseTimeMetrics, LeadStatistics
from app.core.dependencies import get_current_active_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard analytics overview"""
    
    # Total customers
    result = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.user_id == current_user.id
        )
    )
    total_customers = result.scalar() or 0
    
    # Active conversations (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    result = await db.execute(
        select(func.count(Conversation.id))
        .join(Customer)
        .where(
            Customer.user_id == current_user.id,
            Conversation.last_message_at >= week_ago,
            Conversation.is_active == True
        )
    )
    active_conversations = result.scalar() or 0
    
    # Total orders
    result = await db.execute(
        select(func.count(Order.id)).where(
            Order.user_id == current_user.id
        )
    )
    total_orders = result.scalar() or 0
    
    # Total revenue
    result = await db.execute(
        select(func.sum(Order.total_amount)).where(
            Order.user_id == current_user.id,
            Order.status != OrderStatus.CANCELLED
        )
    )
    total_revenue = result.scalar() or 0.0
    
    # Average response time (simplified - in seconds)
    average_response_time = 45.0  # Placeholder
    
    # Leads this week
    result = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.user_id == current_user.id,
            Customer.first_contact_date >= week_ago
        )
    )
    leads_this_week = result.scalar() or 0
    
    # Customers needing attention (inactive > 3 months OR negative sentiment recently)
    three_months_ago = datetime.utcnow() - timedelta(days=90)
    
    # Check for recent negative messages
    recent_negative = select(Conversation.customer_id).join(Message).where(
        Message.sentiment == 'negative',
        Message.created_at >= week_ago
    ).scalar_subquery()
    
    from sqlalchemy import or_
    
    result = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.user_id == current_user.id,
            Customer.is_active == True,
            or_(
                # Scenario 1: Ghosted for 3 months (no orders)
                and_(
                    Customer.last_contact_date < three_months_ago,
                    Customer.total_orders == 0
                ),
                # Scenario 2: Sounded "off" (negative sentiment) recently
                Customer.id.in_(recent_negative)
            )
        )
    )
    customers_needing_attention = result.scalar() or 0
    
    return AnalyticsOverview(
        total_customers=total_customers,
        active_conversations=active_conversations,
        total_orders=total_orders,
        total_revenue=total_revenue,
        average_response_time=average_response_time,
        leads_this_week=leads_this_week,
        customers_needing_attention=customers_needing_attention
    )


@router.get("/response-time", response_model=ResponseTimeMetrics)
async def get_response_time_metrics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get response time metrics"""
    
    # Simplified metrics - in production, calculate from actual message timestamps
    return ResponseTimeMetrics(
        average_response_time=45.0,
        median_response_time=30.0,
        fastest_response=5.0,
        slowest_response=120.0
    )


@router.get("/leads", response_model=LeadStatistics)
async def get_lead_statistics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get lead statistics"""
    
    # Total leads (all customers)
    result = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.user_id == current_user.id
        )
    )
    total_leads = result.scalar() or 0
    
    # Converted leads (customers with orders)
    result = await db.execute(
        select(func.count(Customer.id)).where(
            Customer.user_id == current_user.id,
            Customer.total_orders > 0
        )
    )
    converted_leads = result.scalar() or 0
    
    # Conversion rate
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0.0
    
    # Leads by platform (simplified)
    leads_by_platform = {
        "telegram": total_leads
    }
    
    return LeadStatistics(
        total_leads=total_leads,
        converted_leads=converted_leads,
        conversion_rate=conversion_rate,
        leads_by_platform=leads_by_platform
    )
