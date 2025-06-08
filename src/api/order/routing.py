from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from api.auth.dependency import get_current_user
from api.auth.auth import get_session
from api.order.model import Order, OrderItem
from api.attribute.model import Attribute
from api.product.model import Product
from api.order.scheme import OrderCreate, OrderRead, OrderUpdate
from api.user.model import User


router = APIRouter()

@router.post("/", response_model=OrderRead)
def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    total_price = 0.0
    order_items: List[OrderItem] = []

    # Duyệt qua từng item trong đơn hàng
    for item in order_data.items:
        # Lấy product attribute tương ứng
        attribute = session.exec(
            select(Attribute).where(Attribute.attribute_id == item.attribute_id)
        ).first()
        if not attribute:
            raise HTTPException(status_code=404, detail=f"Product attribute {item.attribute_id} not found")

        if attribute.product_id != item.product_id:
            raise HTTPException(
                status_code=400,
                detail=f"Attribute {item.attribute_id} does not belong to product {item.product_id}"
            )

        if attribute.quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough quantity for attribute {item.attribute_id}. Available: {attribute.quantity}"
            )

        # Lấy giá sản phẩm từ Product
        product = session.exec(
            select(Product).where(Product.product_id == item.product_id)
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")

        item_price = product.price * item.quantity
        total_price += item_price

        # Ghi chú item order
        order_items.append(OrderItem(
            product_id=item.product_id,
            attribute_id=item.attribute_id,
            quantity=item.quantity,
            price=product.price
        ))

        # Trừ tồn kho
        attribute.quantity -= item.quantity
        session.add(attribute)

    # Tạo đơn hàng
    new_order = Order(user_id=current_user.id, total_price=total_price)
    session.add(new_order)
    session.commit()
    session.refresh(new_order)

    # Thêm các OrderItem
    for item in order_items:
        item.order_id = new_order.id
        session.add(item)

    session.commit()
    session.refresh(new_order)
    return new_order

@router.get("/", response_model=List[OrderRead])
def list_orders(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    orders = session.exec(select(Order).where(Order.user_id == current_user.id)).all()
    return orders

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
    order = session.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")

    # Delete old items
    old_items = session.exec(select(OrderItem).where(OrderItem.order_id == order_id)).all()
    for item in old_items:
        session.delete(item)

    total_price = 0.0
    for item in update_data.items:
        product = session.exec(select(Product).where(Product.product_id == item.product_id)).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")

        session.add(OrderItem(
            order_id=order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=product.price
        ))
        total_price += product.price * item.quantity

    order.total_price = total_price
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

    # Xóa các order item trước
    items = session.exec(select(OrderItem).where(OrderItem.order_id == order_id)).all()
    for item in items:
        session.delete(item)

    session.delete(order)
    session.commit()
    return {"message": "Order deleted"}
