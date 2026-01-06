"""
User Profile Management API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import User
from app.schemas import UserResponse, UserUpdate
from app.core.dependencies import get_current_active_user

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user profile
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user profile
    """
    # Fetch fresh user object to ensure session attachment
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one()

    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    
    # Check if telegram_bot_token is being updated (for webhook registration)
    telegram_token_updated = False
    new_bot_token = None
    if 'telegram_bot_token' in update_data and update_data['telegram_bot_token']:
        telegram_token_updated = True
        new_bot_token = update_data['telegram_bot_token'].strip()
        update_data['telegram_bot_token'] = new_bot_token
    
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    
    # Auto-register webhook if bot token was just connected
    if telegram_token_updated and new_bot_token:
        from app.services.messaging.telegram_service import telegram_service
        from app.core.config import settings
        
        # Get webhook base URL from settings
        webhook_base = settings.WEBHOOK_BASE_URL
        
        if webhook_base:
            # Ensure no trailing slash on base URL to avoid double slashes
            webhook_base = webhook_base.rstrip("/")
            webhook_url = f"{webhook_base}/api/webhooks/telegram/{user.id}"
            
            try:
                success = await telegram_service.set_webhook(webhook_url, new_bot_token)
                if not success:
                    # If registration fails, we should probably inform the user
                    # but since the profile is already updated, we can return a 400
                    # to make the frontend show an error
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to register webhook with Telegram. Please check your Bot Token."
                    )
            except HTTPException:
                raise
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to auto-register webhook: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error registering webhook: {str(e)}"
                )
        else:
            # Critical: WEBHOOK_BASE_URL is required for Telegram to work
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="WEBHOOK_BASE_URL is not configured in the backend. This is required for Telegram bots. Please contact support or check server environment variables."
            )
    
    return user
