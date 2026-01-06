"""
Messaging API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from app.db.database import get_db
from app.db.models import User, Customer, Conversation, Message, PlatformType, MessageStatus
from app.schemas import (
    MessageSend, MessageResponse, ConversationResponse,
    ConversationWithMessages
)
from app.core.dependencies import get_current_active_user
from app.services.messaging.telegram_service import telegram_service
from app.services.ai.ai_service import ai_service

router = APIRouter(prefix="/api", tags=["Messaging"])


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all conversations"""
    
    # Get conversations for user's customers with customer name
    result = await db.execute(
        select(Conversation, Customer.name)
        .join(Customer)
        .where(Customer.user_id == current_user.id)
        .order_by(desc(Conversation.last_message_at))
        .offset(skip)
        .limit(limit)
    )
    rows = result.all()
    
    conversations = []
    for conv, customer_name in rows:
        # Populate customer_name manually
        conv.customer_name = customer_name
        conversations.append(conv)
    
    return conversations


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get messages for a conversation"""
    
    # Verify conversation belongs to user
    result = await db.execute(
        select(Conversation)
        .join(Customer)
        .where(
            Conversation.id == conversation_id,
            Customer.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .offset(skip)
        .limit(limit)
    )
    messages = result.scalars().all()
    
    return messages


@router.post("/messages/send", response_model=MessageResponse)
async def send_message(
    message_data: MessageSend,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a message to a customer"""
    
    # Get customer
    result = await db.execute(
        select(Customer).where(
            Customer.id == message_data.customer_id,
            Customer.user_id == current_user.id
        )
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Get or create conversation
    result = await db.execute(
        select(Conversation).where(
            Conversation.customer_id == customer.id,
            Conversation.platform == message_data.platform
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        conversation = Conversation(
            customer_id=customer.id,
            platform=message_data.platform
        )
        db.add(conversation)
        await db.flush()
    
    # Prepare Credentials
    credentials = None
    
    if message_data.platform == PlatformType.TELEGRAM:
        if current_user.telegram_bot_token:
            credentials = {"bot_token": current_user.telegram_bot_token}
        
        # Send via Telegram
        send_result = await telegram_service.send_message(
            chat_id=int(customer.phone_number), # chat_id stored in phone_number
            text=message_data.content,
            credentials=credentials
        )
        # Map telegram result to match generic key for easier handling
        if "message_id" in send_result:
            send_result["message_sid"] = send_result["message_id"]
    else:
        # Unsupported platform for now
        send_result = {"success": False, "error": f"Platform {message_data.platform} not supported"}
    
    # Create message record
    new_message = Message(
        conversation_id=conversation.id,
        content=message_data.content,
        is_from_customer=False,
        ai_generated=False,
        status=MessageStatus.SENT if send_result["success"] else MessageStatus.FAILED,
        platform_message_id=send_result.get("message_sid")
    )
    
    db.add(new_message)
    
    # Update conversation
    conversation.last_message_at = datetime.utcnow()
    
    # Update customer
    customer.last_contact_date = datetime.utcnow()
    
    await db.commit()
    await db.refresh(new_message)
    
    return new_message


@router.get("/webhooks/telegram/{user_id}")
async def check_telegram_webhook(user_id: str):
    """Diagnostic endpoint to verify webhook URL is correctly configured"""
    return {
        "status": "active",
        "message": "Telegram Webhook is Active!",
        "user_id": user_id,
        "instructions": "This URL should be used as your WEBHOOK_BASE_URL (after removing the /api/webhooks/telegram portion) in Render environment settings."
    }


@router.post("/webhooks/telegram/{user_id}", status_code=status.HTTP_200_OK)
async def telegram_webhook(
    user_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle incoming messages from Telegram Bot API.
    Responds immediately with 200 OK to Telegram and processes message in background.
    """
    try:
        # 1. Parse JSON webhook payload
        webhook_data = await request.json()
        
        # 2. Basic validation
        message_obj = webhook_data.get("message", {})
        if not message_obj:
            return {"status": "ok"}
        
        chat_id = message_obj.get("chat", {}).get("id")
        message_text = message_obj.get("text") or message_obj.get("caption", "")
        message_id = message_obj.get("message_id")
        from_user = message_obj.get("from", {})
        first_name = from_user.get("first_name", "User")
        
        # Handle photos (receipts)
        photo = message_obj.get("photo")
        photo_file_id = None
        if photo:
            # photo is a list of PhotoSize, last one is the largest
            photo_file_id = photo[-1].get("file_id")
        
        if not chat_id or (not message_text and not photo_file_id):
            return {"status": "ok"}
            
        # 3. Offload EVERYTHING to background task
        background_tasks.add_task(
            process_telegram_message_complete,
            user_id,
            chat_id,
            message_text,
            message_id,
            first_name,
            photo_file_id
        )
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error in webhook entry point for user {user_id}: {str(e)}")
        # Still return 200 to Telegram to avoid repeated retries
        return {"status": "ok"}


async def process_telegram_message_complete(
    user_id: UUID,
    chat_id: int,
    message_text: str,
    message_id: int,
    first_name: str,
    photo_file_id: Optional[str] = None
):
    """Comprehensive background task: Save incoming, generate AI response, and send back"""
    from app.db.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            # 1. Verify User exists
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                logger.error(f"Webhook received for non-existent user ID: {user_id}")
                return

            # Send typing indicator immediately
            credentials = {"bot_token": user.telegram_bot_token} if user.telegram_bot_token else None
            await telegram_service.send_chat_action(chat_id, "typing", credentials)

            # 2. Find or create customer
            result = await db.execute(
                select(Customer).where(
                    Customer.phone_number == str(chat_id),
                    Customer.user_id == user_id
                )
            )
            customer = result.scalar_one_or_none()
            
            if not customer:
                customer = Customer(
                    user_id=user_id,
                    name=first_name if first_name else "Customer",
                    phone_number=str(chat_id)
                )
                db.add(customer)
                await db.flush()

            # 3. Find or create conversation
            result = await db.execute(
                select(Conversation).where(
                    Conversation.customer_id == customer.id,
                    Conversation.platform == PlatformType.TELEGRAM
                )
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                conversation = Conversation(
                    customer_id=customer.id,
                    platform=PlatformType.TELEGRAM,
                    platform_conversation_id=str(chat_id)
                )
                db.add(conversation)
                await db.flush()

            # 4. Save incoming message
            incoming_message = Message(
                conversation_id=conversation.id,
                content=message_text,
                is_from_customer=True,
                status=MessageStatus.DELIVERED,
                platform_message_id=str(message_id)
            )
            db.add(incoming_message)
            await db.commit() # Commit incoming message first

            # 5. Get conversation history for AI
            result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(desc(Message.created_at))
                .limit(10)
            )
            history = result.scalars().all()
            
            conversation_history = [
                {
                    "content": msg.content,
                    "is_from_customer": msg.is_from_customer
                }
                for msg in reversed(history)
            ]
            
            # 6. Generate AI response
            customer_context = {
                "name": customer.name,
                "total_orders": customer.total_orders,
                "total_spent": customer.total_spent,
                "currency": "NGN",
                "business_profile": {
                    "business_name": user.business_name,
                    "phone_number": user.phone_number,
                    "bank_name": user.bank_name,
                    "account_number": user.account_number,
                    "account_name": user.account_name,
                    "business_context": user.business_context
                }
            }
            
            ai_result = await ai_service.generate_response(
                customer_message=f"{message_text} [PHOTO_RECEIVED]" if photo_file_id else message_text,
                conversation_history=conversation_history,
                customer_context=customer_context
            )
            
            # 7. Save AI response to DB
            ai_message = Message(
                conversation_id=conversation.id,
                content=ai_result["response"],
                is_from_customer=False,
                ai_generated=True,
                intent_detected=ai_result["intent"],
                sentiment=ai_result["sentiment"],
                status=MessageStatus.PENDING
            )
            db.add(ai_message)
            await db.flush()
            
            # Handle photo receipt storage
            receipt_url = None
            if photo_file_id:
                try:
                    from telegram import Bot
                    token = user.telegram_bot_token or settings.TELEGRAM_DEFAULT_BOT_TOKEN
                    async with Bot(token=token) as bot:
                        file = await bot.get_file(photo_file_id)
                        receipt_url = file.file_path # This is the public URL from Telegram servers (valid for ~1hr)
                except Exception as p_err:
                    logger.error(f"Failed to get photo URL: {p_err}")

            # 8. Order Extraction (if any)
            if ai_result.get("extracted_order"):
                try:
                    order_data = ai_result["extracted_order"]
                    import random, string
                    order_num = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                    
                    from app.db.models import Order
                    new_order = Order(
                        user_id=user_id,
                        customer_id=customer.id,
                        order_number=f"ORD-{order_num}",
                        items=order_data.get("items", []),
                        total_amount=order_data.get("total_amount", 0.0),
                        currency=order_data.get("currency", "NGN"),
                        status="pending",
                        receipt_url=receipt_url,
                        notes=f"Auto-generated from chat context"
                    )
                    db.add(new_order)
                    customer.total_orders += 1
                    customer.total_spent += new_order.total_amount
                    await db.flush()
                    
                    # Notify business owner of new order
                    try:
                        from app.services.notifications.notification_service import notification_service
                        await notification_service.notify_new_order(
                            db=db,
                            user_id=str(user_id),
                            customer_name=customer.name,
                            order_number=new_order.order_number,
                            total_amount=new_order.total_amount,
                            items=new_order.items
                        )
                    except Exception as n_err:
                        logger.error(f"Order notification failed: {n_err}")
                except Exception as o_err:
                    logger.error(f"Order extraction failed: {o_err}")

            # 9. Notify Urgent if needed
            if ai_message.intent_detected in ["complaint", "urgent"]:
                try:
                    from app.services.notifications.notification_service import notification_service
                    await notification_service.notify_urgent_inquiry(
                        db, str(user_id), customer.name, message_text
                    )
                except Exception as u_err:
                    logger.error(f"Urgent notification failed: {u_err}")

            # 10. Send response to Telegram
            credentials = {"bot_token": user.telegram_bot_token} if user.telegram_bot_token else None
            send_result = await telegram_service.send_message(
                chat_id=chat_id,
                text=ai_result["response"],
                credentials=credentials
            )
            
            if send_result["success"]:
                ai_message.status = MessageStatus.SENT
                ai_message.platform_message_id = send_result.get("message_id")
            else:
                ai_message.status = MessageStatus.FAILED
                logger.error(f"Telegram send failed for user {user_id}: {send_result.get('error')}")
                
            conversation.last_message_at = datetime.utcnow()
            customer.last_contact_date = datetime.utcnow()
            
            await db.commit()
            logger.info(f"Successfully processed AI response for user {user_id}, chat {chat_id}")

        except Exception as e:
            logger.error(f"Error in complete background processing for user {user_id}: {str(e)}")
            await db.rollback()
