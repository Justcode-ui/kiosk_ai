import asyncio
from datetime import datetime, timedelta
from typing import List
from sqlalchemy import select, func
from celery import shared_task
import logging

from app.db.database import AsyncSessionLocal
from app.db.models import User, Order, Customer
from app.services.notifications.notification_service import notification_service

logger = logging.getLogger(__name__)

@shared_task(name="app.tasks.daily_tasks.send_all_daily_summaries")
def send_all_daily_summaries():
    """Entry point for Celery Beat to trigger summaries for all users"""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.ensure_future(_process_all_summaries())
    else:
        loop.run_until_complete(_process_all_summaries())

async def _process_all_summaries():
    """Async logic to process each user's summary"""
    async with AsyncSessionLocal() as db:
        try:
            # Get all active users
            result = await db.execute(select(User).where(User.is_active == True))
            users = result.scalars().all()
            
            for user in users:
                try:
                    await _send_user_daily_summary(db, user)
                except Exception as e:
                    logger.error(f"Failed to send summary for user {user.id}: {e}")
        except Exception as e:
            logger.error(f"Error in _process_all_summaries: {e}")

async def _send_user_daily_summary(db, user):
    """Calculate and send daily summary for a specific user"""
    # Define "daily" as last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    # 1. Total Orders count and Revenue
    orders_result = await db.execute(
        select(Order)
        .where(Order.user_id == user.id, Order.created_at >= yesterday)
    )
    daily_orders = orders_result.scalars().all()
    
    orders_count = len(daily_orders)
    revenue = sum(o.total_amount for o in daily_orders)
    
    # 2. New Customers count
    customers_result = await db.execute(
        select(func.count(Customer.id))
        .where(Customer.user_id == user.id, Customer.created_at >= yesterday)
    )
    new_customers_count = customers_result.scalar() or 0
    
    # 3. Recent Orders Summary (for the table)
    orders_summary = []
    # Get customer names for these orders
    for order in daily_orders[:10]: # Limit to top 10
        c_result = await db.execute(select(Customer.name).where(Customer.id == order.customer_id))
        customer_name = c_result.scalar() or "Unknown"
        orders_summary.append({
            "number": order.order_number,
            "customer": customer_name,
            "amount": order.total_amount,
            "status": order.status.value if hasattr(order.status, 'value') else str(order.status)
        })
    
    # 4. Send Email
    await notification_service.send_daily_summary(
        user=user,
        orders_count=orders_count,
        revenue=revenue,
        new_customers_count=new_customers_count,
        orders_summary=orders_summary
    )
    logger.info(f"Daily summary sent for user {user.id}")
