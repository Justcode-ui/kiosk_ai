"""
Order Management API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from uuid import UUID
from datetime import datetime
import secrets

from app.db.database import get_db
from app.db.models import User, Customer, Order, OrderStatus
from app.schemas import OrderCreate, OrderUpdate, OrderResponse
from app.core.dependencies import get_current_active_user

router = APIRouter(prefix="/api/orders", tags=["Orders"])


def generate_order_number() -> str:
    """Generate unique order number"""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_part = secrets.token_hex(4).upper()
    return f"ORD-{timestamp}-{random_part}"


@router.get("", response_model=List[OrderResponse])
async def list_orders(
    skip: int = 0,
    limit: int = 100,
    status_filter: OrderStatus = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all orders with customer details"""
    
    # Use select with join to get customer info
    query = select(Order, Customer).join(Customer, Order.customer_id == Customer.id).where(Order.user_id == current_user.id)
    
    if status_filter:
        query = query.where(Order.status == status_filter)
    
    query = query.order_by(desc(Order.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    # manually construct response objects to include customer_name
    orders_response = []
    for order, customer in rows:
        order_dict = {
            "id": order.id,
            "user_id": order.user_id,
            "customer_id": order.customer_id,
            "customer_name": customer.name,  # Add customer name
            "order_number": order.order_number,
            "items": order.items,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "status": order.status,
            "notes": order.notes,
            "receipt_url": order.receipt_url,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "completed_at": order.completed_at
        }
        orders_response.append(order_dict)
    
    return orders_response


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific order"""
    
    result = await db.execute(
        select(Order, Customer)
        .join(Customer, Order.customer_id == Customer.id)
        .where(
            Order.id == order_id,
            Order.user_id == current_user.id
        )
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order, customer = row
    
    # Convert to dict and add customer name
    return {
        "id": order.id,
        "user_id": order.user_id,
        "customer_id": order.customer_id,
        "customer_name": customer.name,
        "order_number": order.order_number,
        "items": order.items,
        "total_amount": order.total_amount,
        "currency": order.currency,
        "status": order.status,
        "notes": order.notes,
        "receipt_url": order.receipt_url,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "completed_at": order.completed_at
    }


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new order"""
    
    # Verify customer exists
    result = await db.execute(
        select(Customer).where(
            Customer.id == order_data.customer_id,
            Customer.user_id == current_user.id
        )
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Calculate total
    total_amount = sum(
        item.price * item.quantity
        for item in order_data.items
    )
    
    # Create order
    new_order = Order(
        user_id=current_user.id,
        customer_id=order_data.customer_id,
        order_number=generate_order_number(),
        items=[item.model_dump() for item in order_data.items],
        total_amount=total_amount,
        notes=order_data.notes
    )
    
    db.add(new_order)
    
    # Update customer stats
    customer.total_orders += 1
    customer.total_spent += total_amount
    customer.last_contact_date = datetime.utcnow()
    
    await db.commit()
    await db.refresh(new_order)
    
    # Return with customer name
    return {
        "id": new_order.id,
        "user_id": new_order.user_id,
        "customer_id": new_order.customer_id,
        "customer_name": customer.name,
        "order_number": new_order.order_number,
        "items": new_order.items,
        "total_amount": new_order.total_amount,
        "currency": new_order.currency,
        "status": new_order.status,
        "notes": new_order.notes,
        "receipt_url": new_order.receipt_url,
        "created_at": new_order.created_at,
        "updated_at": new_order.updated_at,
        "completed_at": new_order.completed_at
    }


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    order_data: OrderUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an order"""
    
    result = await db.execute(
        select(Order, Customer)
        .join(Customer, Order.customer_id == Customer.id)
        .where(
            Order.id == order_id,
            Order.user_id == current_user.id
        )
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order, customer = row
    
    # Update fields
    update_data = order_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    # If status changed to completed, set completed_at
    if order_data.status == OrderStatus.COMPLETED and not order.completed_at:
        order.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(order)
    
    # Return with customer name
    return {
        "id": order.id,
        "user_id": order.user_id,
        "customer_id": order.customer_id,
        "customer_name": customer.name,
        "order_number": order.order_number,
        "items": order.items,
        "total_amount": order.total_amount,
        "currency": order.currency,
        "status": order.status,
        "notes": order.notes,
        "receipt_url": order.receipt_url,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "completed_at": order.completed_at
    }


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an order"""
    
    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user.id
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    await db.delete(order)
    await db.commit()
    
    return None
