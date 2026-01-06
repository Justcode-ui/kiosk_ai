"""
Telegram Bot Service
Handles all Telegram Bot API interactions for customer messaging
"""
import logging
import httpx
from typing import Optional, Dict, Any
from telegram import Bot, Update
from telegram.error import TelegramError
from app.core.config import settings

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for sending messages via Telegram Bot API"""
    
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self.default_bot = None
        if hasattr(settings, 'TELEGRAM_DEFAULT_BOT_TOKEN') and settings.TELEGRAM_DEFAULT_BOT_TOKEN:
            self.default_bot = Bot(
                token=settings.TELEGRAM_DEFAULT_BOT_TOKEN,
                # Note: Bot will create its own client if not provided, but we can share one
            )
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create a persistent httpx client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    def _get_bot(self, credentials: Optional[Dict[str, str]] = None) -> Bot:
        """Get bot instance (user-specific or default)"""
        if credentials and credentials.get('bot_token'):
            return Bot(token=credentials['bot_token'])
        elif self.default_bot:
            return self.default_bot
        else:
            raise ValueError("No Telegram bot configured")
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send a text message to a Telegram chat
        """
        try:
            token = credentials.get('bot_token') if credentials else None
            if not token:
                from app.core.config import settings
                token = settings.TELEGRAM_DEFAULT_BOT_TOKEN
            
            if not token:
                raise ValueError("No Telegram bot token provided")

            client = await self.get_client()
            async with Bot(token=token) as bot:
                # bot.request will use its own internal client if we don't pass one, 
                # but for v20+ we can pass a private client or just trust the context manager.
                # Actually, the 'async with Bot' pattern already handles client lifecycle properly.
                # However, to be persistent across calls, we should ideally keep the Bot instance.
                try:
                    # Try sending with HTML first for nice formatting
                    message = await bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        parse_mode='HTML'
                    )
                except TelegramError as html_err:
                    # Fallback to plain text if HTML parsing fails (common with AI responses)
                    logger.warning(f"HTML send failed, falling back to plain text: {html_err}")
                    message = await bot.send_message(
                        chat_id=chat_id,
                        text=text
                    )
                
                logger.info(f"Message sent to chat_id {chat_id}, message_id: {message.message_id}")
                return {
                    "success": True,
                    "message_id": str(message.message_id)
                }
            
        except TelegramError as e:
            logger.error(f"Telegram error sending message to {chat_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def set_webhook(
        self,
        webhook_url: str,
        bot_token: str
    ) -> bool:
        """
        Set webhook URL for a bot
        """
        try:
            async with Bot(token=bot_token) as bot:
                # First delete existing webhook just in case
                await bot.delete_webhook(drop_pending_updates=True)
                # Then set new one
                success = await bot.set_webhook(url=webhook_url)
                logger.info(f"Webhook set successfully for bot to {webhook_url}: {success}")
                return success
            
        except TelegramError as e:
            logger.error(f"Failed to set webhook: {str(e)}")
            return False
    
    async def delete_webhook(self, bot_token: str) -> bool:
        """Delete webhook (useful for disconnecting)"""
        try:
            async with Bot(token=bot_token) as bot:
                await bot.delete_webhook()
                logger.info("Webhook deleted successfully")
                return True
        except TelegramError as e:
            logger.error(f"Failed to delete webhook: {str(e)}")
            return False

    async def send_chat_action(
        self,
        chat_id: int,
        action: str = "typing",
        credentials: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send a chat action (like 'typing')
        """
        try:
            token = credentials.get('bot_token') if credentials else None
            if not token:
                token = settings.TELEGRAM_DEFAULT_BOT_TOKEN
            
            if not token:
                return False

            async with Bot(token=token) as bot:
                await bot.send_chat_action(chat_id=chat_id, action=action)
                return True
        except Exception as e:
            logger.error(f"Failed to send chat action to {chat_id}: {str(e)}")
            return False


# Global service instance
telegram_service = TelegramService()
