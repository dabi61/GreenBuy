from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, and_
from sqlalchemy import text
from typing import List, Optional, Union
from api.auth.dependency import get_current_user
from api.auth.auth import get_session
from api.auth.permission import require_admin_or_approver
from api.order.model import Order, OrderItem, OrderStatus, generate_order_number
from api.attribute.model import Attribute
from api.product.model import Product
from api.order.scheme import (
    OrderCreate, OrderRead, OrderUpdate, OrderStatusUpdate, 
    OrderSummary, CancelOrderRequest, OrderListResponse
)
from api.user.model import User
from datetime import datetime

router = APIRouter()

def calculate_shipping_fee(total_price: float, shipping_address: str) -> float:
    """
    Tính phí vận chuyển dựa trên tổng giá trị đơn hàng và địa chỉ
    """
    # Miễn phí ship với đơn hàng > 500k
    if total_price >= 500000:
        return 0.0
    
    # Phí ship cơ bản
    base_fee = 30000
    
    # Phí ship khác nhau theo địa chỉ
    if shipping_address and any(city in shipping_address.lower() for city in ["hà nội", "hồ chí minh"]):
        return base_fee
    else:
        return base_fee + 15000  # Phí ship ngoại tỉnh

@router.post("/", response_model=OrderRead)
def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Tạo đơn hàng mới"""
    try:
        total_price = 0.0
        order_items_data = []

        # Validate và tính toán từng item trong đơn hàng
        for item in order_data.items:
            # Lấy product attribute
            attribute = session.exec(
                select(Attribute).where(Attribute.attribute_id == item.attribute_id)
            ).first()
            if not attribute:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Product attribute {item.attribute_id} not found"
                )

            # Validate attribute thuộc product
            if attribute.product_id != item.product_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Attribute {item.attribute_id} does not belong to product {item.product_id}"
                )

            # Kiểm tra tồn kho
            if attribute.quantity < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Not enough quantity for attribute {item.attribute_id}. Available: {attribute.quantity}"
                )

            # Lấy giá sản phẩm
            product = session.exec(
                select(Product).where(Product.product_id == item.product_id)
            ).first()
            if not product:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Product {item.product_id} not found"
                )

            # Tính giá
            item_price = attribute.price * item.quantity
            total_price += item_price

            # Lưu thông tin item để tạo sau
            order_items_data.append({
                'product_id': item.product_id,
                'attribute_id': item.attribute_id,
                'quantity': item.quantity,
                'price': attribute.price,
                'attribute': attribute
            })

        # Tính phí vận chuyển
        shipping_fee = calculate_shipping_fee(total_price, order_data.shipping_address)
        final_amount = total_price + shipping_fee

        # Tạo đơn hàng sử dụng SQLModel ORM với integer status
        order_number = generate_order_number()
        
        # Sử dụng SQLModel ORM với integer status (sau khi migration)
        order = Order(
            order_number=order_number,
            user_id=current_user.id,
            status=OrderStatus.PENDING,  # Integer value (1)
            subtotal=total_price,
            tax_amount=0.0,
            shipping_fee=shipping_fee,
            discount_amount=0.0,
            total_amount=final_amount,
            shipping_address=order_data.shipping_address,
            billing_address=order_data.billing_address,
            phone_number=order_data.phone_number,
            recipient_name=order_data.recipient_name,
            delivery_notes=order_data.delivery_notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(order)
        session.flush()  # Get ID before committing
        
        order_id = order.id

        # Tạo order items và trừ tồn kho
        for item_data in order_items_data:
            # Tạo order item sử dụng SQLModel ORM để tránh constraint conflict
            order_item = OrderItem(
                order_id=order_id,
                product_id=item_data['product_id'],
                attribute_id=item_data['attribute_id'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )
            session.add(order_item)

            # Trừ tồn kho
            item_data['attribute'].quantity -= item_data['quantity']
            session.add(item_data['attribute'])

        session.commit()
        
        # Refresh order object để return
        session.refresh(order)
        return order

    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create order: {str(e)}"
        )

@router.get("/", response_model=OrderListResponse)
def list_orders(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    status_filter: Optional[str] = Query(None, description="Filter by status (can be string like 'pending' or number like '1')"),
    page: int = 1,
    limit: int = 10
):
    """Lấy danh sách đơn hàng của user với phân trang"""
    from sqlmodel import func
    
    # Convert status_filter to integer if provided
    status_filter_int = None
    if status_filter:
        try:
            # Try to parse as integer first
            status_filter_int = int(status_filter)
        except ValueError:
            # If not integer, try to convert from status name to ID
            status_filter_int = OrderStatus.get_id(status_filter.lower())
    
    # Base query
    query = select(Order).where(Order.user_id == current_user.id)
    
    # Filter by status if provided
    if status_filter_int:
        query = query.where(Order.status == status_filter_int)
    
    # Count total
    count_query = select(func.count(Order.id)).where(Order.user_id == current_user.id)
    if status_filter_int:
        count_query = count_query.where(Order.status == status_filter_int)
    total = session.exec(count_query).one()
    
    # Apply pagination and ordering
    query = query.order_by(Order.created_at.desc())
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    orders = session.exec(query).all()
    
    # Calculate pagination metadata
    total_pages = (total + limit - 1) // limit
    has_next = page < total_pages
    has_prev = page > 1
    
    # Convert to summary format
    summaries = []
    for order in orders:
        total_items = len(order.items) if order.items else 0
        summaries.append(OrderSummary(
            id=order.id,
            order_number=order.order_number,
            status=order.get_status_name(),  # Use helper method to get status name
            total_items=total_items,
            total_amount=order.total_amount or 0.0,
            created_at=order.created_at
        ))
    
    return OrderListResponse(
        items=summaries,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )

@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Lấy chi tiết đơn hàng"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return order

@router.put("/{order_id}", response_model=OrderRead)
def update_order(
    order_id: int,
    update_data: OrderUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Cập nhật thông tin đơn hàng (chỉ khi còn pending)"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if not order.is_editable():
        raise HTTPException(
            status_code=400, 
            detail="Cannot update order after confirmation"
        )

    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(order, field, value)
    
    order.updated_at = datetime.utcnow()
    session.add(order)
    session.commit()
    session.refresh(order)
    return order

@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,  # Use request body instead of query parameter
    current_user: User = Depends(require_admin_or_approver),
    session: Session = Depends(get_session)
):
    """Cập nhật trạng thái đơn hàng (chỉ admin/approver)"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    new_status = status_update.status
    
    # Validate status transition
    valid_next_statuses = order.get_valid_next_statuses()
    if new_status not in valid_next_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot transition from {OrderStatus.get_name(order.status)} to {OrderStatus.get_name(new_status)}. Valid transitions: {[OrderStatus.get_name(s) for s in valid_next_statuses]}"
        )

    # Update status và timestamps
    old_status = order.status
    old_status_name = OrderStatus.get_name(old_status)
    new_status_name = OrderStatus.get_name(new_status)
    
    order.status = new_status
    order.updated_at = datetime.utcnow()
    
    # Update admin notes if provided
    if status_update.admin_notes:
        if order.internal_notes:
            order.internal_notes += f" | Admin note: {status_update.admin_notes}"
        else:
            order.internal_notes = f"Admin note: {status_update.admin_notes}"
    
    # Update tracking number if provided (for shipped orders)
    if status_update.tracking_number and new_status == OrderStatus.SHIPPED:
        if order.notes:
            order.notes += f" | Tracking: {status_update.tracking_number}"
        else:
            order.notes = f"Tracking: {status_update.tracking_number}"
    
    # Update cancellation reason if provided (for cancelled orders)
    if status_update.cancellation_reason and new_status == OrderStatus.CANCELLED:
        if order.internal_notes:
            order.internal_notes += f" | Cancellation: {status_update.cancellation_reason}"
        else:
            order.internal_notes = f"Cancellation: {status_update.cancellation_reason}"

    # Set specific timestamps based on new status
    if new_status == OrderStatus.CONFIRMED:
        order.confirmed_at = datetime.utcnow()
    elif new_status == OrderStatus.SHIPPED:
        order.shipped_at = datetime.utcnow()
    elif new_status == OrderStatus.DELIVERED:
        order.delivered_at = datetime.utcnow()
    elif new_status == OrderStatus.CANCELLED:
        order.cancelled_at = datetime.utcnow()
    
    session.add(order)
    session.commit()
    
    return {
        "message": f"Order status updated from {old_status_name} to {new_status_name}",
        "order_id": order.id,
        "old_status": old_status_name,
        "new_status": new_status_name,
        "admin_notes": status_update.admin_notes,
        "tracking_number": status_update.tracking_number,
        "cancellation_reason": status_update.cancellation_reason
    }

@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    cancel_request: CancelOrderRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Hủy đơn hàng (user có thể hủy khi pending/confirmed)"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if not order.is_cancellable():
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel order with status {order.status}"
        )

    try:
        # Hoàn lại inventory
        items = session.exec(select(OrderItem).where(OrderItem.order_id == order_id)).all()
        for item in items:
            attribute = session.get(Attribute, item.attribute_id)
            if attribute:
                attribute.quantity += item.quantity
                session.add(attribute)

        # Update order status to cancelled
        old_status_name = order.get_status_name()
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.utcnow()
        order.updated_at = datetime.utcnow()
        
        # Update internal notes
        if order.internal_notes:
            order.internal_notes += f" | Customer cancellation: {cancel_request.cancellation_reason}"
        else:
            order.internal_notes = f"Customer cancellation: {cancel_request.cancellation_reason}"
        
        session.add(order)
        
        session.commit()
        
        # Return success message with status info
        return {
            "message": f"Order cancelled successfully. Status changed from {old_status_name} to cancelled",
            "order_id": order.id,
            "new_status": "cancelled"
        }

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel order: {str(e)}"
        )

@router.delete("/{order_id}")
def delete_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Xóa đơn hàng (chỉ khi pending hoặc cancelled)"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if order.status not in [OrderStatus.PENDING, OrderStatus.CANCELLED]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete order with status {order.get_status_name()}"
        )

    try:
        # Xóa order items trước
        items = session.exec(select(OrderItem).where(OrderItem.order_id == order_id)).all()
        for item in items:
            session.delete(item)

        # Xóa order
        session.delete(order)
        session.commit()
        
        return {"message": f"Order {order_id} deleted successfully"}

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete order: {str(e)}"
        )
