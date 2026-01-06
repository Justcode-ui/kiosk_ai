"""
Review & Feedback Response Service
Handles sentiment analysis and automated review responses
"""

from typing import Dict, Optional
from datetime import datetime
from groq import Groq

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ReviewResponseService:
    """Service for analyzing reviews and generating responses"""
    
    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
    
    async def analyze_sentiment(self, review_text: str) -> Dict[str, any]:
        """
        Analyze sentiment of a review using Groq LLaMA
        Returns: {
            'sentiment': 'positive' | 'neutral' | 'negative',
            'score': float (0-1),
            'key_points': List[str],
            'urgency': 'low' | 'medium' | 'high'
        }
        """
        try:
            prompt = f"""Analyze the sentiment of this customer review and provide a structured response.

Review: "{review_text}"

Provide your analysis in the following format:
SENTIMENT: [positive/neutral/negative]
SCORE: [0.0 to 1.0, where 1.0 is most positive]
KEY_POINTS: [comma-separated list of main points]
URGENCY: [low/medium/high - how urgently this needs a response]
REASON: [brief explanation of the sentiment]

Be concise and accurate."""

            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sentiment analysis expert. Analyze customer reviews accurately and provide structured insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse the response
            lines = analysis_text.strip().split('\n')
            result = {
                'sentiment': 'neutral',
                'score': 0.5,
                'key_points': [],
                'urgency': 'low',
                'reason': ''
            }
            
            for line in lines:
                if line.startswith('SENTIMENT:'):
                    result['sentiment'] = line.split(':', 1)[1].strip().lower()
                elif line.startswith('SCORE:'):
                    try:
                        result['score'] = float(line.split(':', 1)[1].strip())
                    except:
                        pass
                elif line.startswith('KEY_POINTS:'):
                    points = line.split(':', 1)[1].strip()
                    result['key_points'] = [p.strip() for p in points.split(',')]
                elif line.startswith('URGENCY:'):
                    result['urgency'] = line.split(':', 1)[1].strip().lower()
                elif line.startswith('REASON:'):
                    result['reason'] = line.split(':', 1)[1].strip()
            
            return result
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return {
                'sentiment': 'neutral',
                'score': 0.5,
                'key_points': [],
                'urgency': 'low',
                'reason': 'Analysis failed'
            }
    
    async def generate_review_response(
        self,
        review_text: str,
        sentiment: str,
        business_name: str,
        reviewer_name: Optional[str] = None
    ) -> str:
        """Generate an appropriate response to a review"""
        try:
            name = reviewer_name or "valued customer"
            
            prompt = f"""Generate a professional, empathetic response to this customer review.

Business Name: {business_name}
Reviewer: {name}
Sentiment: {sentiment}
Review: "{review_text}"

Guidelines:
- Be genuine and personal
- Address specific points mentioned in the review
- For positive reviews: Express gratitude and encourage continued patronage
- For neutral reviews: Thank them and ask how to improve
- For negative reviews: Apologize sincerely, acknowledge issues, and offer solutions
- Keep it concise (2-3 sentences)
- Use a warm, professional tone
- End with a call to action or invitation

Generate ONLY the response text, no labels or formatting."""

            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a customer service expert for {business_name}. Write thoughtful, professional responses to customer reviews."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Review response generation failed: {str(e)}")
            # Fallback responses
            if sentiment == 'positive':
                return f"Thank you so much for your kind words! We're thrilled you had a great experience with {business_name}. We look forward to serving you again soon!"
            elif sentiment == 'negative':
                return f"We sincerely apologize for your experience. Your feedback is important to us at {business_name}, and we'd love the opportunity to make things right. Please contact us directly so we can resolve this."
            else:
                return f"Thank you for taking the time to share your feedback with {business_name}. We appreciate your input and are always working to improve. We hope to serve you better next time!"
    
    async def detect_review_triggers(self, review_text: str) -> Dict[str, bool]:
        """
        Detect specific triggers in reviews that need attention
        Returns flags for: refund_request, complaint, praise, question
        """
        text_lower = review_text.lower()
        
        # Refund keywords
        refund_keywords = ['refund', 'money back', 'return', 'reimburse']
        has_refund_request = any(keyword in text_lower for keyword in refund_keywords)
        
        # Complaint keywords
        complaint_keywords = ['terrible', 'awful', 'worst', 'horrible', 'disappointed', 'angry', 'frustrated']
        has_complaint = any(keyword in text_lower for keyword in complaint_keywords)
        
        # Praise keywords
        praise_keywords = ['excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'best', 'great']
        has_praise = any(keyword in text_lower for keyword in praise_keywords)
        
        # Question indicators
        has_question = '?' in review_text
        
        return {
            'refund_request': has_refund_request,
            'complaint': has_complaint,
            'praise': has_praise,
            'question': has_question
        }


# Global review response service instance
review_service = ReviewResponseService()
