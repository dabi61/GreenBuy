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
    OrderSummary, CancelOrderRequest, OrderListResponse,
    OrderForShop, ShopOrderStats, ShopOrderListResponse,
    AdminOrderRead, AdminOrderSummary, AdminOrderListResponse,
    AdminOrderStats, AdminOrderStatusUpdateRequest, AdminOrderFilter
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

            # Tính giá - convert decimal to float
            unit_price = float(attribute.price) if attribute.price else 0.0
            item_price = unit_price * item.quantity
            total_price += item_price

            # Lưu thông tin item để tạo sau
            order_items_data.append({
                'product_id': item.product_id,
                'attribute_id': item.attribute_id,
                'quantity': item.quantity,
                'price': unit_price,
                'attribute': attribute,
                'product': product
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
            attribute = item_data['attribute']
            # Tạo attribute_details từ color và size
            attribute_parts = []
            if attribute.color:
                attribute_parts.append(f"Màu: {attribute.color}")
            if attribute.size:
                attribute_parts.append(f"Size: {attribute.size}")
            attribute_details = " | ".join(attribute_parts) if attribute_parts else "Mặc định"
            
            unit_price = item_data['price']  # Already converted to float above
            order_item = OrderItem(
                order_id=order_id,
                product_id=item_data['product_id'],
                attribute_id=item_data['attribute_id'],
                product_name=item_data['product'].name,
                attribute_details=attribute_details,
                quantity=item_data['quantity'],
                unit_price=unit_price,
                total_price=unit_price * item_data['quantity']
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

@router.get("/shop-orders", response_model=ShopOrderListResponse)
def get_shop_orders(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    limit: int = Query(10, ge=1, le=100, description="Số lượng đơn hàng mỗi trang"),
    date_from: Optional[str] = Query(None, description="Lọc từ ngày (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Lọc đến ngày (YYYY-MM-DD)")
):
    """Lấy tất cả đơn hàng của shop với thống kê chi tiết"""
    from sqlmodel import func, col
    from sqlalchemy import text
    from api.shop.model import Shop
    from datetime import datetime, timedelta
    
    # Kiểm tra user có shop không
    shop = session.exec(select(Shop).where(Shop.user_id == current_user.id)).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found for current user")
    
    # Convert status filter to integer if provided
    status_filter_int = None
    if status_filter:
        try:
            status_filter_int = int(status_filter)
        except ValueError:
            status_filter_int = OrderStatus.get_id(status_filter.lower())
    
    # Parse date filters
    date_from_dt = None
    date_to_dt = None
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format. Use YYYY-MM-DD")
    
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
            # Set to end of day
            date_to_dt = date_to_dt.replace(hour=23, minute=59, second=59)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format. Use YYYY-MM-DD")
    
    # Query để lấy tất cả orders có chứa sản phẩm của shop này
    base_query = text("""
        SELECT DISTINCT o.*
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN product p ON oi.product_id = p.product_id
        WHERE p.shop_id = :shop_id
    """)
    
    # Build dynamic WHERE clauses
    where_clauses = ["p.shop_id = :shop_id"]
    params = {"shop_id": shop.id}
    
    if status_filter_int:
        where_clauses.append("o.status = :status")
        params["status"] = status_filter_int
    
    if date_from_dt:
        where_clauses.append("o.created_at >= :date_from")
        params["date_from"] = date_from_dt
    
    if date_to_dt:
        where_clauses.append("o.created_at <= :date_to")
        params["date_to"] = date_to_dt
    
    # Main query with pagination
    main_query = text(f"""
        SELECT DISTINCT o.*, 
               COALESCE(CONCAT(u.first_name, ' ', u.last_name), u.username, u.email) as customer_full_name,
               COUNT(oi.id) as total_items_in_order
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN product p ON oi.product_id = p.product_id
        JOIN users u ON o.user_id = u.id
        WHERE {' AND '.join(where_clauses)}
        GROUP BY o.id, u.first_name, u.last_name, u.username, u.email
        ORDER BY o.created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    
    # Count query
    count_query = text(f"""
        SELECT COUNT(DISTINCT o.id)
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN product p ON oi.product_id = p.product_id
        WHERE {' AND '.join(where_clauses)}
    """)
    
    # Execute queries
    offset = (page - 1) * limit
    params.update({"limit": limit, "offset": offset})
    
    orders_result = session.execute(main_query, params).fetchall()
    total_count = session.execute(count_query, params).fetchone()[0]
    
    # Prepare response data
    shop_orders = []
    
    for order_row in orders_result:
        # Lấy thông tin chi tiết các sản phẩm của shop trong đơn hàng này
        shop_items_query = text("""
            SELECT p.name as product_name, 
                   oi.quantity, 
                   oi.unit_price,
                   a.color,
                   a.size
            FROM order_items oi
            JOIN product p ON oi.product_id = p.product_id
            LEFT JOIN attribute a ON oi.attribute_id = a.attribute_id
            WHERE oi.order_id = :order_id AND p.shop_id = :shop_id
        """)
        
        shop_items_result = session.execute(shop_items_query, {
            "order_id": order_row.id,
            "shop_id": shop.id
        }).fetchall()
        
        shop_items = []
        shop_subtotal = 0.0
        total_shop_items = 0
        
        for item in shop_items_result:
            # Convert decimal to float to avoid type mismatch
            unit_price = float(item.unit_price) if item.unit_price else 0.0
            item_total = unit_price * item.quantity
            shop_subtotal += item_total
            total_shop_items += item.quantity
            
            # Tạo attribute_name từ color và size
            attribute_parts = []
            if item.color:
                attribute_parts.append(f"Màu: {item.color}")
            if item.size:
                attribute_parts.append(f"Size: {item.size}")
            attribute_name = " | ".join(attribute_parts) if attribute_parts else "Mặc định"
            
            shop_items.append({
                "product_name": item.product_name,
                "attribute_name": attribute_name,
                "quantity": item.quantity,
                "price": unit_price,
                "total": item_total
            })
        
        # Tạo OrderForShop object
        shop_order = OrderForShop(
            id=order_row.id,
            order_number=order_row.order_number,
            status=order_row.status,  # Will be converted by validator
            customer_name=order_row.recipient_name,
            customer_phone=order_row.phone_number,
            shipping_address=order_row.shipping_address,
            total_items=total_shop_items,
            total_amount=order_row.total_amount or 0.0,
            created_at=order_row.created_at,
            updated_at=order_row.updated_at,
            confirmed_at=order_row.confirmed_at,
            shipped_at=order_row.shipped_at,
            delivered_at=order_row.delivered_at,
            cancelled_at=order_row.cancelled_at,
            shop_items=shop_items,
            shop_subtotal=shop_subtotal
        )
        
        shop_orders.append(shop_order)
    
    # Tính toán thống kê cho get_shop_orders
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    
    stats_query = text("""
        SELECT 
            COUNT(DISTINCT o.id) as total_orders,
            COUNT(DISTINCT CASE WHEN o.status = 1 THEN o.id END) as pending_orders,
            COUNT(DISTINCT CASE WHEN o.status = 2 THEN o.id END) as confirmed_orders,
            COUNT(DISTINCT CASE WHEN o.status = 3 THEN o.id END) as processing_orders,
            COUNT(DISTINCT CASE WHEN o.status = 4 THEN o.id END) as shipped_orders,
            COUNT(DISTINCT CASE WHEN o.status = 5 THEN o.id END) as delivered_orders,
            COUNT(DISTINCT CASE WHEN o.status = 6 THEN o.id END) as cancelled_orders,
            COUNT(DISTINCT CASE WHEN o.status = 7 THEN o.id END) as refunded_orders,
            COUNT(DISTINCT CASE WHEN o.status = 8 THEN o.id END) as returned_orders,
            COALESCE(SUM(CASE WHEN o.status = 5 THEN oi.total_price END), 0) as total_revenue,
            COALESCE(SUM(CASE WHEN o.status IN (1,2,3,4) THEN oi.total_price END), 0) as pending_revenue,
            COUNT(DISTINCT CASE WHEN o.created_at >= :today_start THEN o.id END) as orders_today,
            COUNT(DISTINCT CASE WHEN o.created_at >= :week_start THEN o.id END) as orders_this_week,
            COUNT(DISTINCT CASE WHEN o.created_at >= :month_start THEN o.id END) as orders_this_month
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN product p ON oi.product_id = p.product_id
        WHERE p.shop_id = :shop_id
    """)
    
    stats_result = session.execute(stats_query, {
        "shop_id": shop.id,
        "today_start": today_start,
        "week_start": week_start,
        "month_start": month_start
    }).fetchone()
    
    stats = ShopOrderStats(
        total_orders=stats_result.total_orders or 0,
        pending_orders=stats_result.pending_orders or 0,
        confirmed_orders=stats_result.confirmed_orders or 0,
        processing_orders=stats_result.processing_orders or 0,
        shipped_orders=stats_result.shipped_orders or 0,
        delivered_orders=stats_result.delivered_orders or 0,
        cancelled_orders=stats_result.cancelled_orders or 0,
        refunded_orders=stats_result.refunded_orders or 0,
        returned_orders=stats_result.returned_orders or 0,
        total_revenue=float(stats_result.total_revenue or 0),
        pending_revenue=float(stats_result.pending_revenue or 0),
        orders_today=stats_result.orders_today or 0,
        orders_this_week=stats_result.orders_this_week or 0,
        orders_this_month=stats_result.orders_this_month or 0,
        pending_ratings=0  # TODO: Tính toán số rating cần trả lời
    )
    
    # Pagination metadata
    total_pages = (total_count + limit - 1) // limit
    has_next = page < total_pages
    has_prev = page > 1
    
    return ShopOrderListResponse(
        items=shop_orders,
        stats=stats,
        total=total_count,
        page=page,
        limit=limit,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )

@router.get("/shop-stats", response_model=ShopOrderStats)
def get_shop_stats(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Lấy thống kê tổng quan đơn hàng của shop (không bao gồm danh sách chi tiết)"""
    from sqlalchemy import text
    from api.shop.model import Shop
    from datetime import datetime, timedelta
    
    # Kiểm tra user có shop không
    shop = session.exec(select(Shop).where(Shop.user_id == current_user.id)).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found for current user")
    
    # Tính toán thống kê
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    
    stats_query = text("""
        SELECT 
            COUNT(DISTINCT o.id) as total_orders,
            COUNT(DISTINCT CASE WHEN o.status = 1 THEN o.id END) as pending_orders,
            COUNT(DISTINCT CASE WHEN o.status = 2 THEN o.id END) as confirmed_orders,
            COUNT(DISTINCT CASE WHEN o.status = 3 THEN o.id END) as processing_orders,
            COUNT(DISTINCT CASE WHEN o.status = 4 THEN o.id END) as shipped_orders,
            COUNT(DISTINCT CASE WHEN o.status = 5 THEN o.id END) as delivered_orders,
            COUNT(DISTINCT CASE WHEN o.status = 6 THEN o.id END) as cancelled_orders,
            COUNT(DISTINCT CASE WHEN o.status = 7 THEN o.id END) as refunded_orders,
            COUNT(DISTINCT CASE WHEN o.status = 8 THEN o.id END) as returned_orders,
            COALESCE(SUM(CASE WHEN o.status = 5 THEN oi.total_price END), 0) as total_revenue,
            COALESCE(SUM(CASE WHEN o.status IN (1,2,3,4) THEN oi.total_price END), 0) as pending_revenue,
            COUNT(DISTINCT CASE WHEN o.created_at >= :today_start THEN o.id END) as orders_today,
            COUNT(DISTINCT CASE WHEN o.created_at >= :week_start THEN o.id END) as orders_this_week,
            COUNT(DISTINCT CASE WHEN o.created_at >= :month_start THEN o.id END) as orders_this_month
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN product p ON oi.product_id = p.product_id
        WHERE p.shop_id = :shop_id
    """)
    
    stats_result = session.execute(stats_query, {
        "shop_id": shop.id,
        "today_start": today_start,
        "week_start": week_start,
        "month_start": month_start
    }).fetchone()
    
    # TODO: Tính số lượng ratings cần trả lời
    # Có thể thêm query để đếm số ratings chưa có phản hồi từ shop
    pending_ratings_query = text("""
        SELECT COUNT(*) 
        FROM shop_ratings sr
        WHERE sr.shop_id = :shop_id 
        AND sr.id NOT IN (
            SELECT rating_id FROM shop_rating_responses 
            WHERE rating_id = sr.id
        )
    """)
    
    try:
        pending_ratings_result = session.execute(pending_ratings_query, {"shop_id": shop.id}).fetchone()
        pending_ratings_count = pending_ratings_result[0] if pending_ratings_result else 0
    except:
        # Nếu bảng shop_rating_responses chưa tồn tại thì skip
        pending_ratings_count = 0
    
    return ShopOrderStats(
        total_orders=stats_result.total_orders or 0,
        pending_orders=stats_result.pending_orders or 0,
        confirmed_orders=stats_result.confirmed_orders or 0,
        processing_orders=stats_result.processing_orders or 0,
        shipped_orders=stats_result.shipped_orders or 0,
        delivered_orders=stats_result.delivered_orders or 0,
        cancelled_orders=stats_result.cancelled_orders or 0,
        refunded_orders=stats_result.refunded_orders or 0,
        returned_orders=stats_result.returned_orders or 0,
        total_revenue=float(stats_result.total_revenue or 0),
        pending_revenue=float(stats_result.pending_revenue or 0),
        orders_today=stats_result.orders_today or 0,
        orders_this_week=stats_result.orders_this_week or 0,
        orders_this_month=stats_result.orders_this_month or 0,
        pending_ratings=pending_ratings_count
    )

# ===========================
# ORDER ID ENDPOINTS (đặt cuối để tránh conflict với specific routes)
# ===========================

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

# ==================== ADMIN ORDER MANAGEMENT ====================

@router.get("/admin/orders", response_model=AdminOrderListResponse)
def get_admin_orders(
    current_user: User = Depends(require_admin_or_approver),
    session: Session = Depends(get_session),
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    limit: int = Query(10, ge=1, le=100, description="Số lượng order mỗi trang"),
    status: Optional[str] = Query(None, description="Filter theo status order"),
    payment_status: Optional[str] = Query(None, description="Filter theo payment status"),
    date_from: Optional[str] = Query(None, description="Lọc từ ngày (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Lọc đến ngày (YYYY-MM-DD)"),
    customer_search: Optional[str] = Query(None, description="Tìm kiếm khách hàng"),
    order_number: Optional[str] = Query(None, description="Tìm kiếm theo số order"),
    min_amount: Optional[float] = Query(None, description="Giá trị đơn hàng tối thiểu"),
    max_amount: Optional[float] = Query(None, description="Giá trị đơn hàng tối đa"),
):
    """Lấy danh sách tất cả đơn hàng cho admin với filter và pagination"""
    from sqlmodel import func, or_
    from datetime import datetime
    from api.payment.model import Payment, PaymentMethod
    
    # Simplified approach: Get orders first, then get payment info separately
    base_query = select(Order)
    
    # Apply filters
    conditions = []
    
    # Status filter
    if status:
        try:
            status_int = int(status)
            conditions.append(Order.status == status_int)
        except ValueError:
            status_int = OrderStatus.get_id(status.lower())
            conditions.append(Order.status == status_int)
    
    # Date range filter
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            conditions.append(Order.created_at >= date_from_dt)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
            conditions.append(Order.created_at <= date_to_dt)
        except ValueError:
            pass
    
    # Customer search
    if customer_search:
        conditions.append(
            or_(
                Order.recipient_name.ilike(f"%{customer_search}%"),
                Order.phone_number.ilike(f"%{customer_search}%")
            )
        )
    
    # Order number search
    if order_number:
        conditions.append(Order.order_number.ilike(f"%{order_number}%"))
    
    # Amount range
    if min_amount is not None:
        conditions.append(Order.total_amount >= min_amount)
    if max_amount is not None:
        conditions.append(Order.total_amount <= max_amount)
    
    # Apply conditions
    if conditions:
        base_query = base_query.where(and_(*conditions))
    
    # Get all orders first (for payment status filtering)
    all_orders = session.exec(base_query).all()
    
    # Filter by payment status if specified
    filtered_orders = []
    if payment_status:
        for order in all_orders:
            payment = session.exec(
                select(Payment).where(Payment.order_id == order.id)
            ).first()
            
            if payment_status == "pending":
                if not payment or payment.status == "pending":
                    filtered_orders.append(order)
            else:
                if payment and payment.status == payment_status:
                    filtered_orders.append(order)
    else:
        filtered_orders = all_orders
    
    # Calculate pagination
    total = len(filtered_orders)
    offset = (page - 1) * limit
    paginated_orders = filtered_orders[offset:offset + limit]
    
    # Convert to response format with payment info
    items = []
    for order in paginated_orders:
        # Get payment info
        payment = session.exec(
            select(Payment).where(Payment.order_id == order.id)
        ).first()
        
        payment_method = None
        if payment and payment.payment_method_id:
            payment_method = session.exec(
                select(PaymentMethod).where(PaymentMethod.id == payment.payment_method_id)
            ).first()
        
        items.append(AdminOrderSummary(
            id=order.id,
            order_number=order.order_number,
            user_id=order.user_id,
            customer_name=order.recipient_name,
            customer_phone=order.phone_number,
            status=order.status,
            total_amount=order.total_amount,
            payment_status=payment.status if payment else "pending",
            payment_method=payment_method.type if payment_method else None,
            created_at=order.created_at,
            updated_at=order.updated_at
        ))
    
    # Calculate pagination metadata
    total_pages = (total + limit - 1) // limit
    has_next = page < total_pages
    has_prev = page > 1
    
    return AdminOrderListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )

@router.get("/admin/orders/{order_id}", response_model=AdminOrderRead)
def get_admin_order_detail(
    order_id: int,
    current_user: User = Depends(require_admin_or_approver),
    session: Session = Depends(get_session)
):
    """Lấy chi tiết đơn hàng cho admin với thông tin thanh toán"""
    
    # Get order với payment info
    order = session.exec(
        select(Order).where(Order.id == order_id)
    ).first()
    
    if not order:
        raise HTTPException(404, detail="Order not found")
    
    # Get payment info
    from api.payment.model import Payment, PaymentMethod
    payment = session.exec(
        select(Payment).where(Payment.order_id == order_id)
    ).first()
    
    payment_method = None
    if payment and payment.payment_method_id:
        payment_method = session.exec(
            select(PaymentMethod).where(PaymentMethod.id == payment.payment_method_id)
        ).first()
    
    # Get customer info
    customer = session.exec(
        select(User).where(User.id == order.user_id)
    ).first()
    
    # Get order items
    items = session.exec(
        select(OrderItem).where(OrderItem.order_id == order_id)
    ).all()
    
    # Convert to response
    return AdminOrderRead(
        id=order.id,
        order_number=order.order_number,
        user_id=order.user_id,
        customer_name=order.recipient_name,
        customer_email=customer.email if customer else None,
        customer_phone=order.phone_number,
        status=order.status,
        subtotal=order.subtotal,
        tax_amount=order.tax_amount,
        shipping_fee=order.shipping_fee,
        discount_amount=order.discount_amount,
        total_amount=order.total_amount,
        shipping_address=order.shipping_address,
        billing_address=order.billing_address,
        delivery_notes=order.delivery_notes,
        payment_status=payment.status if payment else None,
        payment_method=payment_method.type if payment_method else None,
        payment_amount=payment.amount if payment else None,
        transaction_id=payment.transaction_id if payment else None,
        created_at=order.created_at,
        updated_at=order.updated_at,
        confirmed_at=order.confirmed_at,
        shipped_at=order.shipped_at,
        delivered_at=order.delivered_at,
        cancelled_at=order.cancelled_at,
        items=items,
        notes=order.notes,
        internal_notes=order.internal_notes
    )

@router.patch("/admin/orders/{order_id}/status", response_model=AdminOrderRead)
def update_admin_order_status(
    order_id: int,
    status_update: AdminOrderStatusUpdateRequest,
    current_user: User = Depends(require_admin_or_approver),
    session: Session = Depends(get_session)
):
    """Admin cập nhật status đơn hàng"""
    
    order = session.exec(
        select(Order).where(Order.id == order_id)
    ).first()
    
    if not order:
        raise HTTPException(404, detail="Order not found")
    
    # Validate status transition
    valid_next_statuses = order.get_valid_next_statuses()
    if status_update.status not in valid_next_statuses and status_update.status != order.status:
        current_status_name = OrderStatus.get_name(order.status)
        valid_names = [OrderStatus.get_name(s) for s in valid_next_statuses]
        raise HTTPException(
            400, 
            detail=f"Invalid status transition from {current_status_name} to {OrderStatus.get_name(status_update.status)}. Valid next statuses: {valid_names}"
        )
    
    # Update status
    old_status = order.status
    order.status = status_update.status
    order.updated_at = datetime.utcnow()
    
    # Update internal notes
    if status_update.internal_notes:
        order.internal_notes = status_update.internal_notes
    
    # Update timestamps based on status
    now = datetime.utcnow()
    if status_update.status == OrderStatus.CONFIRMED:
        order.confirmed_at = now
    elif status_update.status == OrderStatus.SHIPPED:
        order.shipped_at = now
    elif status_update.status == OrderStatus.DELIVERED:
        order.delivered_at = now
    elif status_update.status == OrderStatus.CANCELLED:
        order.cancelled_at = now
    
    session.add(order)
    session.commit()
    session.refresh(order)
    
    # TODO: Implement notification to customer if status_update.notify_customer is True
    
    return get_admin_order_detail(order_id, current_user, session)

@router.get("/admin/stats", response_model=AdminOrderStats)
def get_admin_order_stats(
    current_user: User = Depends(require_admin_or_approver),
    session: Session = Depends(get_session)
):
    """Lấy thống kê tổng quan đơn hàng cho admin"""
    from sqlmodel import func
    from datetime import datetime, timedelta
    
    # Total orders
    total_orders = session.exec(select(func.count(Order.id))).one()
    
    # Orders by status
    pending_orders = session.exec(select(func.count(Order.id)).where(Order.status == OrderStatus.PENDING)).one()
    confirmed_orders = session.exec(select(func.count(Order.id)).where(Order.status == OrderStatus.CONFIRMED)).one()
    processing_orders = session.exec(select(func.count(Order.id)).where(Order.status == OrderStatus.PROCESSING)).one()
    shipped_orders = session.exec(select(func.count(Order.id)).where(Order.status == OrderStatus.SHIPPED)).one()
    delivered_orders = session.exec(select(func.count(Order.id)).where(Order.status == OrderStatus.DELIVERED)).one()
    cancelled_orders = session.exec(select(func.count(Order.id)).where(Order.status == OrderStatus.CANCELLED)).one()
    refunded_orders = session.exec(select(func.count(Order.id)).where(Order.status == OrderStatus.REFUNDED)).one()
    returned_orders = session.exec(select(func.count(Order.id)).where(Order.status == OrderStatus.RETURNED)).one()
    
    # Payment stats (using raw SQL to avoid enum issues)
    paid_count = session.exec(
        text("SELECT COUNT(*) FROM orders o JOIN payment p ON o.id = p.order_id WHERE p.status = 'completed'")
    ).first()
    paid_orders = paid_count if paid_count else 0
    
    failed_count = session.exec(
        text("SELECT COUNT(*) FROM orders o JOIN payment p ON o.id = p.order_id WHERE p.status = 'failed'")
    ).first()
    failed_payments = failed_count if failed_count else 0
    
    unpaid_orders = total_orders - paid_orders
    
    # Revenue stats
    total_revenue_result = session.exec(
        text("SELECT COALESCE(SUM(o.total_amount), 0) FROM orders o JOIN payment p ON o.id = p.order_id WHERE p.status = 'completed'")
    ).first()
    total_revenue = float(total_revenue_result) if total_revenue_result else 0.0
    
    pending_revenue_result = session.exec(
        text("SELECT COALESCE(SUM(o.total_amount), 0) FROM orders o LEFT JOIN payment p ON o.id = p.order_id WHERE p.status IS NULL OR p.status != 'completed'")
    ).first()
    pending_revenue = float(pending_revenue_result) if pending_revenue_result else 0.0
    
    # Time-based stats
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    orders_today = session.exec(
        select(func.count(Order.id)).where(func.date(Order.created_at) == today)
    ).one()
    
    orders_this_week = session.exec(
        select(func.count(Order.id)).where(func.date(Order.created_at) >= week_ago)
    ).one()
    
    orders_this_month = session.exec(
        select(func.count(Order.id)).where(func.date(Order.created_at) >= month_ago)
    ).one()
    
    # Average order value
    avg_order_value = 0.0
    if total_orders > 0:
        avg_result = session.exec(select(func.avg(Order.total_amount))).one()
        avg_order_value = float(avg_result) if avg_result else 0.0
    
    return AdminOrderStats(
        total_orders=total_orders,
        pending_orders=pending_orders,
        confirmed_orders=confirmed_orders,
        processing_orders=processing_orders,
        shipped_orders=shipped_orders,
        delivered_orders=delivered_orders,
        cancelled_orders=cancelled_orders,
        refunded_orders=refunded_orders,
        returned_orders=returned_orders,
        paid_orders=paid_orders,
        unpaid_orders=unpaid_orders,
        failed_payments=failed_payments,
        total_revenue=total_revenue,
        pending_revenue=pending_revenue,
        orders_today=orders_today,
        orders_this_week=orders_this_week,
        orders_this_month=orders_this_month,
        avg_order_value=avg_order_value
    )

@router.get("/admin/orders/by-payment-status/{payment_status}", response_model=AdminOrderListResponse)
def get_orders_by_payment_status(
    payment_status: str,
    current_user: User = Depends(require_admin_or_approver),
    session: Session = Depends(get_session),
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    limit: int = Query(10, ge=1, le=100, description="Số lượng order mỗi trang"),
):
    """Lấy đơn hàng theo trạng thái thanh toán"""
    from sqlmodel import func
    from api.payment.model import Payment, PaymentMethod
    
    # Validate payment status
    valid_statuses = ["pending", "processing", "completed", "failed", "cancelled", "refunded", "partially_refunded"]
    if payment_status not in valid_statuses:
        raise HTTPException(400, detail=f"Invalid payment status. Valid values: {valid_statuses}")
    
    # Get all orders
    all_orders = session.exec(select(Order)).all()
    
    # Filter orders by payment status
    filtered_orders = []
    for order in all_orders:
        payment = session.exec(
            select(Payment).where(Payment.order_id == order.id)
        ).first()
        
        if payment_status == "pending":
            if not payment or payment.status == "pending":
                filtered_orders.append(order)
        else:
            if payment and payment.status == payment_status:
                filtered_orders.append(order)
    
    # Sort by created_at desc
    filtered_orders.sort(key=lambda x: x.created_at, reverse=True)
    
    # Calculate pagination
    total = len(filtered_orders)
    offset = (page - 1) * limit
    paginated_orders = filtered_orders[offset:offset + limit]
    
    # Convert to response format
    items = []
    for order in paginated_orders:
        # Get payment info
        payment = session.exec(
            select(Payment).where(Payment.order_id == order.id)
        ).first()
        
        payment_method = None
        if payment and payment.payment_method_id:
            payment_method = session.exec(
                select(PaymentMethod).where(PaymentMethod.id == payment.payment_method_id)
            ).first()
        
        items.append(AdminOrderSummary(
            id=order.id,
            order_number=order.order_number,
            user_id=order.user_id,
            customer_name=order.recipient_name,
            customer_phone=order.phone_number,
            status=order.status,
            total_amount=order.total_amount,
            payment_status=payment.status if payment else "pending",
            payment_method=payment_method.type if payment_method else None,
            created_at=order.created_at,
            updated_at=order.updated_at
        ))
    
    # Calculate pagination metadata
    total_pages = (total + limit - 1) // limit
    has_next = page < total_pages
    has_prev = page > 1
    
    return AdminOrderListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )
