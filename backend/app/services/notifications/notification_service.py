"""
Real-time Notification Service
Handles email, SMS, and WebSocket notifications for important events
"""

from typing import List, Optional
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# from twilio.rest import Client (Removed)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.models import User, Customer, Message, Order
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via multiple channels"""
    
    def __init__(self):
        # Twilio SMS disabled
        pass
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send email notification using SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = settings.SMTP_FROM_EMAIL
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add plain text part
            msg.attach(MIMEText(body, 'plain'))
            
            # Add HTML part if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def notify_urgent_inquiry(
        self,
        db: AsyncSession,
        user_id: str,
        customer_name: str,
        message_content: str
    ):
        """Notify business owner of urgent customer inquiry"""
        # Get user details
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return
        
        # Email notification
        subject = f"🚨 Urgent Inquiry from {customer_name}"
        body = f"""
Hello {user.business_name},

You have received an urgent inquiry from {customer_name}:

"{message_content}"

Please respond as soon as possible.

Best regards,
KioskAI Team
        """
        
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #0D1B2A;">
    <h2 style="color: #1B6EA8;">🚨 Urgent Inquiry</h2>
    <p>Hello <strong>{user.business_name}</strong>,</p>
    <p>You have received an urgent inquiry from <strong>{customer_name}</strong>:</p>
    <blockquote style="background: #E3E6EB; padding: 15px; border-left: 4px solid #4CD7B4; margin: 20px 0;">
        {message_content}
    </blockquote>
    <p>Please respond as soon as possible.</p>
    <p style="color: #77808B; font-size: 12px;">Best regards,<br>KioskAI Team</p>
</body>
</html>
        """
        
        await self.send_email(user.email, subject, body, html_body)
    
    async def notify_refund_request(
        self,
        db: AsyncSession,
        user_id: str,
        customer_name: str,
        order_number: str,
        amount: float
    ):
        """Notify business owner of refund request"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return
        
        subject = f"💰 Refund Request - Order {order_number}"
        body = f"""
Hello {user.business_name},

{customer_name} has requested a refund for Order #{order_number}
Amount: ₦{amount:,.2f}

Please review and process this request.

Best regards,
KioskAI Team
        """
        
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #0D1B2A;">
    <h2 style="color: #D4A055;">💰 Refund Request</h2>
    <p>Hello <strong>{user.business_name}</strong>,</p>
    <p><strong>{customer_name}</strong> has requested a refund:</p>
    <ul style="background: #E3E6EB; padding: 20px; border-radius: 8px;">
        <li>Order: <strong>#{order_number}</strong></li>
        <li>Amount: <strong>₦{amount:,.2f}</strong></li>
    </ul>
    <p>Please review and process this request.</p>
    <p style="color: #77808B; font-size: 12px;">Best regards,<br>KioskAI Team</p>
</body>
</html>
        """
        
        await self.send_email(user.email, subject, body, html_body)
    
    async def notify_high_value_lead(
        self,
        db: AsyncSession,
        user_id: str,
        customer_name: str,
        estimated_value: float,
        message_content: str
    ):
        """Notify business owner of high-value lead"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return
        
        subject = f"🌟 High-Value Lead: {customer_name}"
        body = f"""
Hello {user.business_name},

You have a high-value lead!

Customer: {customer_name}
Estimated Value: ₦{estimated_value:,.2f}

Message: "{message_content}"

Don't miss this opportunity!

Best regards,
KioskAI Team
        """
        
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #0D1B2A;">
    <h2 style="color: #4CD7B4;">🌟 High-Value Lead Detected!</h2>
    <p>Hello <strong>{user.business_name}</strong>,</p>
    <p>You have a high-value lead:</p>
    <div style="background: linear-gradient(135deg, #4CD7B4, #1B6EA8); padding: 20px; border-radius: 8px; color: white; margin: 20px 0;">
        <p><strong>Customer:</strong> {customer_name}</p>
        <p><strong>Estimated Value:</strong> ₦{estimated_value:,.2f}</p>
    </div>
    <blockquote style="background: #E3E6EB; padding: 15px; border-left: 4px solid #4CD7B4; margin: 20px 0;">
        {message_content}
    </blockquote>
    <p><strong>Don't miss this opportunity!</strong></p>
    <p style="color: #77808B; font-size: 12px;">Best regards,<br>KioskAI Team</p>
</body>
</html>
        """
        
        await self.send_email(user.email, subject, body, html_body)


    async def notify_new_order(
        self,
        db: AsyncSession,
        user_id: str,
        customer_name: str,
        order_number: str,
        total_amount: float,
        items: List[dict]
    ):
        """Notify business owner of new order"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return
        
        # Format items string
        items_list = ""
        html_items_list = ""
        for item in items:
            name = item.get('name', 'Unknown Item')
            qty = item.get('quantity', 1)
            price = item.get('price', 0)
            items_list += f"- {name} (x{qty}) - ₦{price:,.2f}\n"
            html_items_list += f"<li>{name} (x{qty}) - ₦{price:,.2f}</li>"

        subject = f"🔔 New Order Received: {order_number}"
        body = f"""
Hello {user.business_name},

You have received a new order from {customer_name}!

Order #{order_number}
Total: ₦{total_amount:,.2f}

Items:
{items_list}

Please login to your dashboard to view details and process this order.

Best regards,
KioskAI Team
        """
        
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #0D1B2A;">
    <h2 style="color: #4CD7B4;">🔔 New Order Received!</h2>
    <p>Hello <strong>{user.business_name}</strong>,</p>
    <p>You have received a new order from <strong>{customer_name}</strong>!</p>
    
    <div style="background: #F8F9FA; padding: 20px; border-radius: 8px; border: 1px solid #E3E6EB; margin: 20px 0;">
        <h3 style="margin-top: 0;">Order #{order_number}</h3>
        <p style="font-size: 18px; font-weight: bold; color: #1B6EA8;">Total: ₦{total_amount:,.2f}</p>
        <hr style="border: 0; border-top: 1px solid #E3E6EB;">
        <p><strong>Items:</strong></p>
        <ul>
            {html_items_list}
        </ul>
    </div>

    <p><a href="https://kioskai-app.onrender.com" style="background: #1B6EA8; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Dashboard</a></p>
    
    <p style="color: #77808B; font-size: 12px;">Best regards,<br>KioskAI Team</p>
</body>
</html>
        """
        
        await self.send_email(user.email, subject, body, html_body)

    async def send_daily_summary(
        self,
        user: User,
        orders_count: int,
        revenue: float,
        new_customers_count: int,
        orders_summary: List[dict]
    ):
        """Send daily summary of business activity"""
        subject = f"📊 Daily Business Summary - {datetime.utcnow().strftime('%Y-%m-%d')}"
        
        order_rows = ""
        for order in orders_summary:
            order_rows += f"<tr><td>{order['number']}</td><td>{order['customer']}</td><td>₦{order['amount']:,.2f}</td><td>{order['status']}</td></tr>"

        body = f"""
Hello {user.business_name},

Here is your daily summary for {datetime.utcnow().strftime('%Y-%m-%d')}:

- New Orders: {orders_count}
- Total Revenue: ₦{revenue:,.2f}
- New Customers: {new_customers_count}

Best regards,
KioskAI Team
        """
        
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #0D1B2A;">
    <h2 style="color: #1B6EA8;">📊 Daily Business Summary</h2>
    <p>Hello <strong>{user.business_name}</strong>,</p>
    
    <div style="display: flex; gap: 20px; margin: 20px 0;">
        <div style="background: #F8F9FA; padding: 15px; border-radius: 8px; flex: 1; text-align: center; border: 1px solid #E3E6EB;">
            <p style="margin: 0; color: #77808B;">New Orders</p>
            <p style="font-size: 24px; font-weight: bold; margin: 5px 0;">{orders_count}</p>
        </div>
        <div style="background: #F8F9FA; padding: 15px; border-radius: 8px; flex: 1; text-align: center; border: 1px solid #E3E6EB;">
            <p style="margin: 0; color: #77808B;">Revenue</p>
            <p style="font-size: 24px; font-weight: bold; margin: 5px 0; color: #4CD7B4;">₦{revenue:,.2f}</p>
        </div>
        <div style="background: #F8F9FA; padding: 15px; border-radius: 8px; flex: 1; text-align: center; border: 1px solid #E3E6EB;">
            <p style="margin: 0; color: #77808B;">New Customers</p>
            <p style="font-size: 24px; font-weight: bold; margin: 5px 0;">{new_customers_count}</p>
        </div>
    </div>

    {f'''
    <h3>Recent Orders</h3>
    <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
        <thead>
            <tr style="background: #E3E6EB; text-align: left;">
                <th style="padding: 10px; border: 1px solid #CBD2D9;">Order #</th>
                <th style="padding: 10px; border: 1px solid #CBD2D9;">Customer</th>
                <th style="padding: 10px; border: 1px solid #CBD2D9;">Amount</th>
                <th style="padding: 10px; border: 1px solid #CBD2D9;">Status</th>
            </tr>
        </thead>
        <tbody>
            {order_rows}
        </tbody>
    </table>
    ''' if orders_summary else '<p>No orders recorded today.</p>'}

    <p style="margin-top: 30px;"><a href="{settings.WEBHOOK_BASE_URL or '#'}" style="background: #1B6EA8; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Dashboard</a></p>
    
    <p style="color: #77808B; font-size: 12px; margin-top: 30px;">Best regards,<br>KioskAI Team</p>
</body>
</html>
        """
        
        await self.send_email(user.email, subject, body, html_body)


# Global notification service instance
notification_service = NotificationService()
