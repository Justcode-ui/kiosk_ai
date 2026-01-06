"""
API Routes for Reviews and Feedback
Handles review submission, sentiment analysis, and automated responses
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime

from app.core.dependencies import get_current_active_user, get_db
from app.db.models import User, Review
from app.services.reviews.review_service import review_service
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


# Pydantic Schemas
class ReviewCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=200)
    review_text: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)
    source: str = Field(default="manual")  # manual, google, facebook, etc.


class ReviewResponse(BaseModel):
    id: str
    customer_name: str
    review_text: str
    rating: int
    sentiment: str
    sentiment_score: float
    urgency: str
    ai_response: str
    response_approved: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SentimentAnalysis(BaseModel):
    sentiment: str
    score: float
    key_points: List[str]
    urgency: str
    reason: str


@router.post("/analyze", response_model=dict)
async def analyze_review(
    review: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a review for sentiment analysis and get automated response
    """
    # Analyze sentiment
    sentiment_analysis = await review_service.analyze_sentiment(review.review_text)
    
    # Generate automated response
    ai_response = await review_service.generate_review_response(
        review_text=review.review_text,
        sentiment=sentiment_analysis['sentiment'],
        business_name=current_user.business_name,
        reviewer_name=review.customer_name
    )
    
    # Detect triggers
    triggers = await review_service.detect_review_triggers(review.review_text)
    
    # Create review record
    new_review = Review(
        user_id=current_user.id,
        customer_name=review.customer_name,
        review_text=review.review_text,
        rating=review.rating,
        source=review.source,
        sentiment=sentiment_analysis['sentiment'],
        sentiment_score=sentiment_analysis['score'],
        urgency=sentiment_analysis['urgency'],
        ai_response=ai_response,
        response_approved=False,
        has_refund_request=triggers['refund_request'],
        has_complaint=triggers['complaint']
    )
    
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    
    return {
        "review_id": str(new_review.id),
        "sentiment_analysis": sentiment_analysis,
        "ai_response": ai_response,
        "triggers": triggers,
        "requires_urgent_attention": sentiment_analysis['urgency'] == 'high' or triggers['refund_request']
    }


@router.get("/", response_model=List[ReviewResponse])
async def list_reviews(
    skip: int = 0,
    limit: int = 50,
    sentiment: str = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all reviews with optional sentiment filter
    """
    query = select(Review).where(Review.user_id == current_user.id)
    
    if sentiment:
        query = query.where(Review.sentiment == sentiment)
    
    query = query.order_by(desc(Review.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    reviews = result.scalars().all()
    
    return reviews


@router.post("/{review_id}/approve", response_model=dict)
async def approve_response(
    review_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve an AI-generated response for a review
    """
    result = await db.execute(
        select(Review).where(
            Review.id == review_id,
            Review.user_id == current_user.id
        )
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    review.response_approved = True
    review.response_sent_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": "Response approved and ready to send",
        "review_id": str(review.id),
        "response": review.ai_response
    }


@router.post("/{review_id}/regenerate", response_model=dict)
async def regenerate_response(
    review_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerate AI response for a review
    """
    result = await db.execute(
        select(Review).where(
            Review.id == review_id,
            Review.user_id == current_user.id
        )
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Generate new response
    new_response = await review_service.generate_review_response(
        review_text=review.review_text,
        sentiment=review.sentiment,
        business_name=current_user.business_name,
        reviewer_name=review.customer_name
    )
    
    review.ai_response = new_response
    review.response_approved = False
    
    await db.commit()
    
    return {
        "message": "Response regenerated successfully",
        "review_id": str(review.id),
        "new_response": new_response
    }


@router.get("/stats", response_model=dict)
async def get_review_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get review statistics and sentiment breakdown
    """
    result = await db.execute(
        select(Review).where(Review.user_id == current_user.id)
    )
    reviews = result.scalars().all()
    
    total = len(reviews)
    if total == 0:
        return {
            "total_reviews": 0,
            "sentiment_breakdown": {},
            "average_rating": 0,
            "pending_responses": 0
        }
    
    sentiment_counts = {}
    total_rating = 0
    pending_responses = 0
    
    for review in reviews:
        sentiment_counts[review.sentiment] = sentiment_counts.get(review.sentiment, 0) + 1
        total_rating += review.rating
        if not review.response_approved:
            pending_responses += 1
    
    return {
        "total_reviews": total,
        "sentiment_breakdown": sentiment_counts,
        "average_rating": round(total_rating / total, 2),
        "pending_responses": pending_responses,
        "urgent_reviews": len([r for r in reviews if r.urgency == 'high'])
    }
