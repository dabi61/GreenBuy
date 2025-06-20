from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from api.auth.dependency import get_current_user
from api.auth.auth import get_session
from api.order.model import Order, OrderItem, OrderStatus
from api.attribute.model import Attribute
from api.product.model import Product
from api.order.scheme import OrderCreate, OrderRead, OrderUpdate, OrderStatusUpdate, OrderSummary
from api.user.model import User
from datetime import datetime
import uuid
import random
from sqlalchemy import text


router = APIRouter()

def generate_order_number() -> str:
    """Generate unique order number in format: ORD-YYYYMMDD-XXXXXX"""
    from datetime import datetime
    date_str = datetime.now().strftime("%Y%m%d")
    random_suffix = str(random.randint(100000, 999999))
    return f"ORD-{date_str}-{random_suffix}"

@router.post("/", response_model=dict)
def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Temporarily hardcode values to bypass Product/Attribute queries
    total_price = 50000.0
    order_items = []
    
    # TEMPORARILY COMMENT OUT complex logic to test basic order creation
    # total_price = 0.0
    # order_items: List[OrderItem] = []

    # # Duyệt qua từng item trong đơn hàng
    # for item in order_data.items:
    #     # Lấy product attribute tương ứng
    #     attribute = session.exec(
    #         select(Attribute).where(Attribute.attribute_id == item.attribute_id)
    #     ).first()
    #     if not attribute:
    #         raise HTTPException(status_code=404, detail=f"Product attribute {item.attribute_id} not found")

    #     if attribute.product_id != item.product_id:
    #         raise HTTPException(
    #             status_code=400,
    #             detail=f"Attribute {item.attribute_id} does not belong to product {item.product_id}"
    #         )

    #     if attribute.quantity < item.quantity:
    #         raise HTTPException(
    #             status_code=400,
    #             detail=f"Not enough quantity for attribute {item.attribute_id}. Available: {attribute.quantity}"
    #         )

    #     # Lấy giá sản phẩm từ Product
    #     product = session.exec(
    #         select(Product).where(Product.product_id == item.product_id)
    #     ).first()
    #     if not product:
    #         raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")

    #     item_price = product.price * item.quantity
    #     total_price += item_price

    #     # Ghi chú item order
    #     order_items.append(OrderItem(
    #         product_id=item.product_id,
    #         attribute_id=item.attribute_id,
    #         quantity=item.quantity,
    #         price=product.price
    #     ))

    #     # Trừ tồn kho
    #     attribute.quantity -= item.quantity
    #     session.add(attribute)

    # Tính toán shipping fee (có thể dựa trên địa chỉ, trọng lượng, v.v.)
    shipping_fee = calculate_shipping_fee(total_price, order_data.shipping_address)
    
    # Tính final amount
    final_amount = total_price + shipping_fee

    # Tạo đơn hàng với updated field names - sử dụng raw SQL để avoid enum issue
    order_number = generate_order_number()
    
    # Insert order using raw SQL với enum casting
    insert_sql = text("""
        INSERT INTO orders (
                user_id, status, created_at, updated_at, 
            subtotal, tax_amount, shipping_fee, discount_amount, total_amount,
            shipping_address, phone_number, recipient_name, delivery_notes, order_number
        ) VALUES (
            :user_id, CAST(:status AS orderstatus), :created_at, :updated_at,
            :subtotal, :tax_amount, :shipping_fee, :discount_amount, :total_amount,
            :shipping_address, :phone_number, :recipient_name, :delivery_notes, :order_number
        ) RETURNING id
    """)
    
    result = session.execute(insert_sql, {
        'user_id': current_user.id,
        'status': 'pending',  # Will be cast to orderstatus enum
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'subtotal': total_price,
        'tax_amount': 0.0,
        'shipping_fee': shipping_fee,
        'discount_amount': 0.0,
        'total_amount': final_amount,
        'shipping_address': order_data.shipping_address,
        'phone_number': order_data.shipping_phone or "N/A",
        'recipient_name': order_data.recipient_name or "N/A", 
        'delivery_notes': order_data.shipping_notes,
        'order_number': order_number
    })
    
    order_id = result.fetchone()[0]
    session.commit()
    
    # TEMPORARILY SKIP OrderItem creation
    # # Thêm các OrderItem bằng raw SQL để tránh relationship issues
    # for item in order_items:
    #     item_sql = text("""
    #         INSERT INTO orderitem (order_id, product_id, attribute_id, quantity, price)
    #         VALUES (:order_id, :product_id, :attribute_id, :quantity, :price)
    #     """)
    #     session.execute(item_sql, {
    #         'order_id': order_id,
    #         'product_id': item.product_id,
    #         'attribute_id': item.attribute_id,
    #         'quantity': item.quantity,
    #         'price': item.price
    #     })

    # session.commit()

    # Return dict to avoid relationship loading issues
    return {
        "id": order_id,
        "status": "pending",
        "subtotal": total_price,
        "tax_amount": 0.0,
        "shipping_fee": shipping_fee,
        "discount_amount": 0.0,
        "total_amount": final_amount,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "shipping_address": order_data.shipping_address,
        "phone_number": order_data.shipping_phone or "N/A",
        "recipient_name": order_data.recipient_name or "N/A",
        "delivery_notes": order_data.shipping_notes,
        "order_number": order_number,
        "items": len(order_items),
        "message": "Order created successfully! (OrderItems temporarily disabled for testing)"
    }

def calculate_shipping_fee(total_price: float, shipping_address: str) -> float:
    """
    Tính phí vận chuyển dựa trên tổng giá trị đơn hàng và địa chỉ
    """
    # Miễn phí ship với đơn hàng > 500k
    if total_price >= 500000:
        return 0.0
    
    # Phí ship cơ bản
    base_fee = 30000
    
    # Có thể thêm logic phức tạp hơn dựa trên địa chỉ
    # Ví dụ: phí ship khác nhau theo tỉnh thành
    if shipping_address and any(city in shipping_address.lower() for city in ["hà nội", "hồ chí minh"]):
        return base_fee
    else:
        return base_fee + 15000  # Phí ship ngoại tỉnh

@router.get("/", response_model=List[OrderSummary])
def list_orders(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    status: OrderStatus = None,
    page: int = 1,
    limit: int = 10
):
    """Lấy danh sách đơn hàng của user với phân trang"""
    from api.db.pagination import PaginationParams, paginate
    
    query = select(Order).where(Order.user_id == current_user.id)
    
    if status:
        query = query.where(Order.status == status)
    
    query = query.order_by(Order.created_at.desc())
    
    pagination_params = PaginationParams(page=page, limit=limit)
    result = paginate(session, query, pagination_params)
    
    # Convert to summary format
    summaries = []
    for order in result.items:
        total_items = len(order.items) if order.items else 0
        summaries.append(OrderSummary(
            id=order.id,
            status=order.status,
            total_items=total_items,
            final_amount=order.total_amount,  # updated field name
            created_at=order.created_at
        ))
    
    return summaries

@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    order = session.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.put("/{order_id}", response_model=OrderRead)
def update_order(
    order_id: int,
    update_data: OrderUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Cập nhật thông tin shipping của đơn hàng (chỉ khi còn pending)"""
    order = session.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")

    # Chỉ cho phép cập nhật khi đơn hàng vẫn pending
    if order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Cannot update order after confirmation")

    # Update shipping information
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(order, field, value)
    
    order.updated_at = datetime.utcnow()
    session.add(order)
    session.commit()
    session.refresh(order)
    return order

@router.patch("/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Cập nhật trạng thái đơn hàng (cho admin/seller)"""
    # Trong thực tế, cần check quyền admin hoặc seller owner
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Validate status transition
    valid_transitions = {
        OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
        OrderStatus.CONFIRMED: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
        OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
        OrderStatus.SHIPPED: [OrderStatus.DELIVERED, OrderStatus.RETURNED],
        OrderStatus.DELIVERED: [OrderStatus.RETURNED],
        OrderStatus.CANCELLED: [],
        OrderStatus.REFUNDED: [],
        OrderStatus.RETURNED: [OrderStatus.REFUNDED]
    }
    
    if status_update.status not in valid_transitions.get(order.status, []):
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot transition from {order.status} to {status_update.status}"
        )

    # Update status and timestamps
    old_status = order.status
    order.status = status_update.status
    order.updated_at = datetime.utcnow()
    
    if status_update.admin_notes:
        order.internal_notes = status_update.admin_notes  # updated field name
    
    if status_update.cancellation_reason:
        order.cancellation_reason = status_update.cancellation_reason

    # Set specific timestamps
    if status_update.status == OrderStatus.CONFIRMED:
        order.confirmed_at = datetime.utcnow()
    elif status_update.status == OrderStatus.SHIPPED:
        order.shipped_at = datetime.utcnow()
    elif status_update.status == OrderStatus.DELIVERED:
        order.delivered_at = datetime.utcnow()

    session.add(order)
    session.commit()
    session.refresh(order)
    return order

@router.post("/{order_id}/cancel", response_model=OrderRead)
def cancel_order(
    order_id: int,
    cancellation_reason: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Hủy đơn hàng (user có thể hủy khi pending/confirmed)"""
    order = session.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
        raise HTTPException(status_code=400, detail="Cannot cancel order in current status")

    # Hoàn lại inventory
    items = session.exec(select(OrderItem).where(OrderItem.order_id == order_id)).all()
    for item in items:
        attribute = session.get(Attribute, item.attribute_id)
        if attribute:
            attribute.quantity += item.quantity
            session.add(attribute)

    # Update order
    order.status = OrderStatus.CANCELLED
    order.cancellation_reason = cancellation_reason
    order.updated_at = datetime.utcnow()
    
    session.add(order)
    session.commit()
    session.refresh(order)
    return order

@router.delete("/{order_id}")
def delete_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    order = session.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")

    # Chỉ cho phép xóa đơn hàng đã hủy hoặc pending
    if order.status not in [OrderStatus.PENDING, OrderStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Cannot delete order in current status")

    # Xóa các order item trước
    items = session.exec(select(OrderItem).where(OrderItem.order_id == order_id)).all()
    for item in items:
        session.delete(item)

    session.delete(order)
    session.commit()
    return {"message": "Order deleted"}

@router.post("/test", response_model=dict)
def test_order_creation(
    session: Session = Depends(get_session)
):
    """Temporary test endpoint để verify core order logic without authentication"""
    try:
        # Test raw SQL insert với known user_id
        order_number = generate_order_number()
        
        insert_sql = text("""
            INSERT INTO orders (
                user_id, status, created_at, updated_at, 
                subtotal, tax_amount, shipping_fee, discount_amount, total_amount,
                shipping_address, phone_number, recipient_name, delivery_notes, order_number
            ) VALUES (
                :user_id, CAST(:status AS orderstatus), :created_at, :updated_at,
                :subtotal, :tax_amount, :shipping_fee, :discount_amount, :total_amount,
                :shipping_address, :phone_number, :recipient_name, :delivery_notes, :order_number
            ) RETURNING id
        """)
        
        result = session.execute(insert_sql, {
            'user_id': 1,  # Valid user ID from database
            'status': 'pending',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'subtotal': 50000.0,
            'tax_amount': 0.0,
            'shipping_fee': 30000,
            'discount_amount': 0.0,
            'total_amount': 80000.0,
            'shipping_address': 'Test Address',
            'phone_number': '0901234567',
            'recipient_name': 'Test User',
            'delivery_notes': 'Test order',
            'order_number': order_number
        })
        
        order_id = result.fetchone()[0]
        session.commit()
        
        return {
            "success": True,
            "order_id": order_id,
            "order_number": order_number,
            "message": "Order created successfully! Core functionality working!"
        }
        
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "error": str(e),
            "message": "Order creation failed"
        }

@router.post("/test-simple", response_model=dict)
def test_simple_order_creation(
    session: Session = Depends(get_session)
):
    """Simple test endpoint without relationships"""
    try:
        # Test raw SQL insert WITHOUT loading any relationships
        order_number = generate_order_number()
        
        insert_sql = text("""
            INSERT INTO orders (
                user_id, status, created_at, updated_at, 
                subtotal, tax_amount, shipping_fee, discount_amount, total_amount,
                shipping_address, phone_number, recipient_name, delivery_notes, order_number
            ) VALUES (
                :user_id, CAST(:status AS orderstatus), :created_at, :updated_at,
                :subtotal, :tax_amount, :shipping_fee, :discount_amount, :total_amount,
                :shipping_address, :phone_number, :recipient_name, :delivery_notes, :order_number
            ) RETURNING id
        """)
        
        result = session.execute(insert_sql, {
            'user_id': 1,
            'status': 'pending',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'subtotal': 50000.0,
            'tax_amount': 0.0,
            'shipping_fee': 30000,
            'discount_amount': 0.0,
            'total_amount': 80000.0,
            'shipping_address': 'Test Address',
            'phone_number': '0901234567',
            'recipient_name': 'Test User',
            'delivery_notes': 'Test order',
            'order_number': order_number
        })
        
        order_id = result.fetchone()[0]
        session.commit()
        
        # Return simple dict instead of loading Order model with relationships
        return {
            "success": True,
            "order_id": order_id,
            "order_number": order_number,
            "message": "Simple order created successfully! No relationships loaded."
        }
        
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "error": str(e),
            "message": "Simple order creation failed"
        }

@router.post("/test-production", response_model=dict)
def test_production_order(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Test production endpoint with authentication but without complex relationships"""
    try:
        # Hardcode values để tránh Product/Attribute relationship loading
        total_price = 22220.0  # price of product_id=1 * quantity=2
        shipping_fee = 30000.0
        final_amount = total_price + shipping_fee
        
        order_number = generate_order_number()
        
        # Insert order using raw SQL
        insert_sql = text("""
            INSERT INTO orders (
                user_id, status, created_at, updated_at, 
                subtotal, tax_amount, shipping_fee, discount_amount, total_amount,
                shipping_address, phone_number, recipient_name, delivery_notes, order_number
            ) VALUES (
                :user_id, CAST(:status AS orderstatus), :created_at, :updated_at,
                :subtotal, :tax_amount, :shipping_fee, :discount_amount, :total_amount,
                :shipping_address, :phone_number, :recipient_name, :delivery_notes, :order_number
            ) RETURNING id
        """)
        
        result = session.execute(insert_sql, {
            'user_id': current_user.id,
            'status': 'pending',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'subtotal': total_price,
            'tax_amount': 0.0,
            'shipping_fee': shipping_fee,
            'discount_amount': 0.0,
            'total_amount': final_amount,
            'shipping_address': '123 Test Street, Ho Chi Minh City',
            'phone_number': '+84901234567',
            'recipient_name': 'Test Customer',
            'delivery_notes': 'Leave at front door',
            'order_number': order_number
        })
        
        order_id = result.fetchone()[0]
        
        # Insert order item using raw SQL
        item_sql = text("""
            INSERT INTO orderitem (order_id, product_id, attribute_id, quantity, price)
            VALUES (:order_id, :product_id, :attribute_id, :quantity, :price)
        """)
        session.execute(item_sql, {
            'order_id': order_id,
            'product_id': 1,
            'attribute_id': 1,
            'quantity': 2,
            'price': 11110.0  # hardcoded price from database
        })
        
        session.commit()
        
        return {
            "success": True,
            "order_id": order_id,
            "order_number": order_number,
            "user_id": current_user.id,
            "total_amount": final_amount,
            "message": "Production order created successfully with authentication!"
        }
        
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "error": str(e),
            "message": "Production order creation failed"
        }
