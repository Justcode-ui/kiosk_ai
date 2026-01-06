"""
Follow-up Tasks
Celery tasks for automated customer follow-ups
"""
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from app.tasks.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.db.models import User, Customer, FollowUp
from app.services.messaging.telegram_service import telegram_service
from app.services.ai.prompts import FOLLOW_UP_INACTIVE_TEMPLATE
from app.core.config import settings


@celery_app.task(name="app.tasks.follow_up_tasks.check_inactive_customers")
def check_inactive_customers():
    """Check for inactive customers and send follow-ups"""
    import asyncio
    asyncio.run(_check_inactive_customers())


async def _check_inactive_customers():
    """Async implementation of inactive customer check"""
    if not settings.AUTO_FOLLOW_UP_ENABLED:
        return
    
    async with AsyncSessionLocal() as db:
        # Find customers inactive for configured hours
        inactive_threshold = datetime.utcnow() - timedelta(
            hours=settings.FOLLOW_UP_DELAY_HOURS
        )
        
        # Optimized query: Join with User to get bot credentials and filter for businesses with bots
        result = await db.execute(
            select(Customer, User).join(User, Customer.user_id == User.id).where(
                and_(
                    Customer.last_contact_date < inactive_threshold,
                    Customer.is_active == True,
                    Customer.total_orders == 0,
                    User.telegram_bot_token.isnot(None) # Only businesses with bots
                )
            )
        )
        inactive_records = result.all()
        
        for customer, user in inactive_records:
            # Check if follow-up already sent recently
            result = await db.execute(
                select(FollowUp).where(
                    and_(
                        FollowUp.customer_id == customer.id,
                        FollowUp.reason == "inactive",
                        FollowUp.created_at > inactive_threshold
                    )
                )
            )
            existing_followup = result.scalar_one_or_none()
            
            if existing_followup:
                continue
            
            # Create follow-up message
            message = FOLLOW_UP_INACTIVE_TEMPLATE.format(
                customer_name=customer.name
            )
            
            credentials = {"bot_token": user.telegram_bot_token}

            # Send via Telegram (chat_id stored in phone_number)
            try:
                # chat_id must be int. We store it in phone_number field for Telegram customers.
                chat_id_int = int(customer.phone_number)
                send_result = await telegram_service.send_message(
                    chat_id=chat_id_int,
                    text=message,
                    credentials=credentials
                )
            except (ValueError, TypeError) as e:
                import logging
                logging.getLogger(__name__).warning(f"Invalid chat_id {customer.phone_number} for customer {customer.id}: {e}")
                continue
            
            if send_result.get("success"):
                # Record follow-up
                follow_up = FollowUp(
                    customer_id=customer.id,
                    message=message,
                    scheduled_for=datetime.utcnow(),
                    is_sent=True,
                    sent_at=datetime.utcnow(),
                    reason="inactive"
                )
                db.add(follow_up)
                
                # Update customer contact date
                customer.last_contact_date = datetime.utcnow()
                await db.flush() # Flush to handle multiple customers in same commit
        
        await db.commit()
        print(f"✅ Processed {len(inactive_records)} potential follow-ups")
