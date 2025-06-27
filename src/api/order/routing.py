from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, and_
from sqlalchemy import text
from typing import List, Optional
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

        # Tạo đơn hàng sử dụng raw SQL để handle enum casting
        order_number = generate_order_number()
        
        insert_sql = text("""
            INSERT INTO "order" (
                user_id, status, created_at, updated_at,
                total_price, shipping_fee, discount_amount, final_amount,
                shipping_address, shipping_phone, recipient_name, shipping_notes
            ) VALUES (
                :user_id, CAST(:status AS orderstatus), :created_at, :updated_at,
                :total_price, :shipping_fee, :discount_amount, :final_amount,
                :shipping_address, :shipping_phone, :recipient_name, :shipping_notes
            ) RETURNING id
        """)
        
        result = session.execute(insert_sql, {
            'user_id': current_user.id,
            'status': 'PENDING',  # Use uppercase to match database enum
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'total_price': total_price,
            'shipping_fee': shipping_fee,
            'discount_amount': 0.0,
            'final_amount': final_amount,
            'shipping_address': order_data.shipping_address,
            'shipping_phone': order_data.phone_number,
            'recipient_name': order_data.recipient_name,
            'shipping_notes': order_data.delivery_notes
        })
        
        order_id = result.fetchone()[0]

        # Tạo order items và trừ tồn kho
        for item_data in order_items_data:
            # Tạo order item sử dụng raw SQL
            item_sql = text("""
                INSERT INTO orderitem (order_id, product_id, attribute_id, quantity, price)
                VALUES (:order_id, :product_id, :attribute_id, :quantity, :price)
            """)
            session.execute(item_sql, {
                'order_id': order_id,
                'product_id': item_data['product_id'],
                'attribute_id': item_data['attribute_id'],
                'quantity': item_data['quantity'],
                'price': item_data['price']
            })

            # Trừ tồn kho
            item_data['attribute'].quantity -= item_data['quantity']
            session.add(item_data['attribute'])

        session.commit()
        
        # Load order object để return
        order = session.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=500, detail="Failed to retrieve created order")
        
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
    status_filter: Optional[OrderStatus] = None,
    page: int = 1,
    limit: int = 10
):
    """Lấy danh sách đơn hàng của user với phân trang"""
    from sqlmodel import func
    
    # Base query
    query = select(Order).where(Order.user_id == current_user.id)
    
    # Filter by status if provided
    if status_filter:
        query = query.where(Order.status == status_filter.value)
    
    # Count total
    count_query = select(func.count(Order.id)).where(Order.user_id == current_user.id)
    if status_filter:
        count_query = count_query.where(Order.status == status_filter.value)
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
            status=order.status,
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
    status_update: OrderStatusUpdate,
    current_user: User = Depends(require_admin_or_approver),
    session: Session = Depends(get_session)
):
    """Cập nhật trạng thái đơn hàng (chỉ admin/approver)"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Validate status transition
    valid_next_statuses = order.get_valid_next_statuses()
    if status_update.status.value not in valid_next_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot transition from {order.status} to {status_update.status.value}. Valid transitions: {valid_next_statuses}"
        )

    # Update status và timestamps sử dụng raw SQL
    old_status = order.status
    
    # Prepare notes update
    new_internal_notes = order.internal_notes or ""
    
    if status_update.admin_notes:
        if new_internal_notes:
            new_internal_notes += f" | Admin: {status_update.admin_notes}"
        else:
            new_internal_notes = f"Admin: {status_update.admin_notes}"
    
    if status_update.cancellation_reason:
        if new_internal_notes:
            new_internal_notes += f" | Cancellation: {status_update.cancellation_reason}"
        else:
            new_internal_notes = f"Cancellation: {status_update.cancellation_reason}"

    # Prepare timestamp updates
    update_params = {
        'order_id': order.id,
        'status': status_update.status.value,  # This will be uppercase now
        'updated_at': datetime.utcnow(),
        'internal_notes': new_internal_notes,
        'confirmed_at': order.confirmed_at,
        'shipped_at': order.shipped_at,
        'delivered_at': order.delivered_at,
        'cancelled_at': order.cancelled_at
    }

    # Set specific timestamps
    if status_update.status == OrderStatus.CONFIRMED:
        update_params['confirmed_at'] = datetime.utcnow()
    elif status_update.status == OrderStatus.SHIPPED:
        update_params['shipped_at'] = datetime.utcnow()
    elif status_update.status == OrderStatus.DELIVERED:
        update_params['delivered_at'] = datetime.utcnow()
    elif status_update.status == OrderStatus.CANCELLED:
        update_params['cancelled_at'] = datetime.utcnow()

    # Update using raw SQL with enum casting
    update_sql = text("""
        UPDATE "order" SET
            status = CAST(:status AS orderstatus),
            updated_at = :updated_at,
            internal_notes = :internal_notes,
            confirmed_at = :confirmed_at,
            shipped_at = :shipped_at,
            delivered_at = :delivered_at,
            cancelled_at = :cancelled_at
        WHERE id = :order_id
    """)
    
    session.execute(update_sql, update_params)
    session.commit()
    
    return {
        "message": f"Order status updated from {old_status} to {order.status}",
        "order_id": order.id,
        "old_status": old_status,
        "new_status": order.status
    }

@router.post("/{order_id}/cancel", response_model=OrderRead)
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

        # Update order sử dụng raw SQL
        # Prepare internal notes
        new_internal_notes = order.internal_notes or ""
        if new_internal_notes:
            new_internal_notes += f" | Customer cancellation: {cancel_request.cancellation_reason}"
        else:
            new_internal_notes = f"Customer cancellation: {cancel_request.cancellation_reason}"
        
        # Update using raw SQL with enum casting
        update_sql = text("""
            UPDATE "order" SET
                status = CAST(:status AS orderstatus),
                cancelled_at = :cancelled_at,
                updated_at = :updated_at,
                internal_notes = :internal_notes
            WHERE id = :order_id
        """)
        
        session.execute(update_sql, {
            'order_id': order.id,
            'status': 'CANCELLED',  # Use uppercase to match database enum
            'cancelled_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'internal_notes': new_internal_notes
        })
        
        session.commit()
        
        # Load updated order để return
        updated_order = session.get(Order, order.id)
        return updated_order

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

    if order.status not in [OrderStatus.PENDING.value, OrderStatus.CANCELLED.value]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete order with status {order.status}"
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
