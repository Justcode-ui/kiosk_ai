"""
AI Service using Groq API
Handles conversation understanding and response generation
"""
import httpx
from typing import List, Dict, Optional
from app.core.config import settings


class GroqAIService:
    """AI service for generating responses using Groq"""
    
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.api_endpoint = settings.GROQ_API_ENDPOINT
        self.model = settings.GROQ_MODEL
        self.temperature = settings.AI_TEMPERATURE
        self.max_tokens = settings.AI_MAX_TOKENS
        self._client: Optional[httpx.AsyncClient] = None
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create a persistent httpx client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        """Close the persistent client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def generate_response(
        self,
        customer_message: str,
        conversation_history: List[Dict[str, str]],
        customer_context: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Generate AI response to customer message
        
        Args:
            customer_message: The customer's message
            conversation_history: Recent conversation messages
            customer_context: Customer information (name, orders, etc.)
        
        Returns:
            Dict with response, intent, and sentiment
        """
        # Build system prompt
        system_prompt = self._build_system_prompt(customer_context)
        
        # Build messages for API
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history
        for msg in conversation_history[-settings.CONVERSATION_MEMORY_LIMIT:]:
            messages.append({
                "role": "user" if msg["is_from_customer"] else "assistant",
                "content": msg["content"]
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": customer_message
        })
        
        try:
            client = await self.get_client()
            response = await client.post(
                self.api_endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                },
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            ai_response = data["choices"][0]["message"]["content"]
            
            # Extract Order JSON if present
            extracted_order = None
            if "<ORDER>" in ai_response and "</ORDER>" in ai_response:
                try:
                    import json
                    import re
                    
                    # regex to extract content between tags
                    match = re.search(r'<ORDER>(.*?)</ORDER>', ai_response, re.DOTALL)
                    if match:
                        json_str = match.group(1).strip()
                        extracted_order = json.loads(json_str)
                        
                        # Remove the order block from the response sent to user
                        ai_response = ai_response.replace(match.group(0), "").strip()
                except Exception as parse_error:
                    print(f"Error parsing order JSON: {parse_error}")
            
            # Detect intent and sentiment
            intent = await self._detect_intent(customer_message)
            sentiment = await self._analyze_sentiment(customer_message)
            
            return {
                "response": ai_response,
                "intent": intent,
                "sentiment": sentiment,
                "extracted_order": extracted_order
            }
        
        except Exception as e:
            print(f"Error generating AI response: {e}")
            # Fallback response
            return {
                "response": "Thank you for your message! I'll get back to you shortly.",
                "intent": "unknown",
                "sentiment": "neutral"
            }
    
    def _build_system_prompt(self, customer_context: Optional[Dict] = None) -> str:
        """Build system prompt with business context"""
        base_prompt = """You are KioskAI, a helpful,accurate and on point AI assistant for a business.
Your role is to:
- Respond professionally and warmly to customer inquiries
- Help customers with product information, orders, and general questions
- Be concise but friendly in your responses
- If you don't know something, politely say so and offer to connect them with a human
- Always maintain a helpful, positive tone

Important guidelines:
- Keep responses under 3-4 sentences when possible
- Use simple, clear language
- Be empathetic and understanding
- Never make promises you can't keep 
- Never hallucinate 
- PRE-VALIDATION: If a customer wants to place an order, you MUST first ask them to send a payment receipt. 
- DO NOT generate an <ORDER> block until the customer mentions they have paid AND you have acknowledged a receipt (as a user message or image description).
- When the customer says they have paid, ask for the payment receipt if you haven't seen one yet.
- Look carefully at the number the customer is using before providing contact details
"""
        
        if customer_context:
            context_info = f"""
Customer Information:
- Name: {customer_context.get('name', 'Customer')}
- Previous orders: {customer_context.get('total_orders', 0)}
- Total spent: {customer_context.get('currency', 'NGN')} {customer_context.get('total_spent', 0)}
"""
            base_prompt += context_info
            
        # Add Business Context if provided
        # We expect customer_context or a separate dict to contain 'business_profile'
        business_profile = customer_context.get('business_profile') if customer_context else None
        
        if business_profile:
            business_info = f"""
Your Business Identity:
- Business Name: {business_profile.get('business_name')}
- Support Phone: {business_profile.get('phone_number')}
- Bank Name: {business_profile.get('bank_name')}
- Account Number: {business_profile.get('account_number')}
- Account Name: {business_profile.get('account_name')}

Instructions for Payment:
If the customer indicates they want to pay or asks for payment details, YOU MUST provide the Bank Name and Account Number listed above. 
Do not invent account numbers. Use the exact ones provided here.

ORDER EXTRACTION INSTRUCTIONS:
If the user has provided a receipt (or confirmed payment and you are moving to record it), you MUST include a JSON block at the end of your response inside <ORDER> tags.
Format:
<ORDER>
{{
  "items": [{{"name": "Product Name", "quantity": 1, "price": 0, "currency": "NGN"}}],
  "total_amount": 0,
  "currency": "NGN",
  "status": "pending",
  "receipt_confirmed": true
}}
</ORDER>
Examples:
- "I've sent the money, here is the record" -> (Confirm items and amount) -> Add <ORDER> block.
- "I want to buy 2 Sneakers for 50k" -> "Great! Please send the payment receipt to our bank details above so I can process your order." (DO NOT ADD <ORDER> BLOCK YET)
"""
            base_prompt += business_info
            
            # Business Knowledge Base
            if business_profile.get('business_context'):
                kb_info = f"""
Business Knowledge Base (Use this to answer questions about products, prices, etc.):
{business_profile.get('business_context')}
"""
                base_prompt += kb_info
        
        return base_prompt
    
    async def _detect_intent(self, message: str) -> str:
        """Detect customer intent from message"""
        message_lower = message.lower()
        
        # Simple keyword-based intent detection
        if any(word in message_lower for word in ["price", "cost", "how much", "pay"]):
            return "pricing_inquiry"
        elif any(word in message_lower for word in ["order", "buy", "purchase", "want"]):
            return "order_intent"
        elif any(word in message_lower for word in ["track", "status", "where", "delivery"]):
            return "order_tracking"
        elif any(word in message_lower for word in ["problem", "issue", "complaint", "wrong"]):
            return "complaint"
        elif any(word in message_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return "greeting"
        else:
            return "general_inquiry"
    
    async def _analyze_sentiment(self, message: str) -> str:
        """Analyze message sentiment"""
        message_lower = message.lower()
        
        # Simple sentiment analysis
        positive_words = ["thank", "great", "good", "excellent", "happy", "love", "perfect"]
        negative_words = ["bad", "poor", "terrible", "angry", "disappointed", "worst", "hate"]
        
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    async def summarize_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Generate a summary of conversation"""
        if not messages:
            return ""
        
        conversation_text = "\n".join([
            f"{'Customer' if msg['is_from_customer'] else 'AI'}: {msg['content']}"
            for msg in messages
        ])
        
        summary_prompt = f"""Summarize this conversation , focusing on:
- What the customer wanted
- What was discussed
- Any action items or outcomes

Conversation:
{conversation_text}

Summary:"""
        
        try:
            client = await self.get_client()
            response = await client.post(
                self.api_endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": summary_prompt}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 150
                },
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
        
        except Exception as e:
            print(f"Error summarizing conversation: {e}")
            return "Conversation summary unavailable"


# Global AI service instance
ai_service = GroqAIService()
