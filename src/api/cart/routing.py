from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from api.auth.dependency import get_current_user
from api.auth.auth import get_session
from api.user.model import User
from api.cart.model import Cart, CartItem
from api.product.model import Product
from api.shop.model import Shop
from api.cart.scheme import CartShopGroup, CartItemRead, UpdateCartItemQuantity, CartItemCreate

router = APIRouter()

@router.get("/me", response_model=List[CartShopGroup])
def get_my_cart(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    cart = session.exec(select(Cart).where(Cart.user_id == current_user.id)).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    cart_items = session.exec(
        select(CartItem).where(CartItem.cart_id == cart.id)
    ).all()

    # Nhóm theo shop
    shop_groups = {}
    for item in cart_items:
        product = session.get(Product, item.product_id)
        if not product:
            continue

        shop = session.get(Shop, product.shop_id)
        if not shop:
            continue

        if shop.id not in shop_groups:
            shop_groups[shop.id] = {
                "shop_id": shop.id,
                "shop_name": shop.name,
                "items": []
            }

        shop_groups[shop.id]["items"].append(CartItemRead(
            product_id=product.product_id,
            product_name=product.name,
            quantity=item.quantity
        ))

    return list(shop_groups.values())


@router.delete("/shop/{shop_id}")
def delete_items_by_shop(
    shop_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    cart = session.exec(select(Cart).where(Cart.user_id == current_user.id)).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    # Lấy tất cả product_id thuộc shop đó
    products = session.exec(
        select(Product.product_id).where(Product.shop_id == shop_id)
    ).all()
    product_ids = [p[0] for p in products]

    if not product_ids:
        raise HTTPException(status_code=404, detail="No products found for this shop")

    # Xoá tất cả cart items khớp
    deleted = session.exec(
        select(CartItem)
        .where(CartItem.cart_id == cart.id)
        .where(CartItem.product_id.in_(product_ids))
    ).all()

    for item in deleted:
        session.delete(item)
    session.commit()

    return {"message": f"Deleted {len(deleted)} items from shop {shop_id}"}

@router.delete("/product/{product_id}")
def delete_cart_item(
    product_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    cart = session.exec(select(Cart).where(Cart.user_id == current_user.id)).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    item = session.exec(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id
        )
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    session.delete(item)
    session.commit()
    return {"message": "Item deleted successfully"}

@router.put("/product/{product_id}")
def update_cart_item_quantity(
    product_id: int,
    update_data: UpdateCartItemQuantity,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if update_data.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")

    cart = session.exec(select(Cart).where(Cart.user_id == current_user.id)).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    item = session.exec(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id
        )
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    item.quantity = update_data.quantity
    session.add(item)
    session.commit()
    session.refresh(item)

    return {"message": "Quantity updated", "product_id": product_id, "quantity": item.quantity}


@router.post("/add", summary="Thêm sản phẩm vào giỏ hàng")
def add_to_cart(
    item: CartItemCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Lấy cart của user, tạo mới nếu chưa có
    cart = session.exec(select(Cart).where(Cart.user_id == current_user.id)).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        session.add(cart)
        session.commit()
        session.refresh(cart)

    # Kiểm tra sản phẩm có tồn tại không
    product = session.exec(select(Product).where(Product.product_id == item.product_id)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")

    # Kiểm tra xem sản phẩm đã có trong giỏ chưa (theo cart_id và product_id)
    existing_item = session.exec(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == item.product_id
        )
    ).first()

    if existing_item:
        existing_item.quantity += item.quantity
        session.add(existing_item)
    else:
        new_item = CartItem(
            cart_id=cart.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        session.add(new_item)

    session.commit()
    return {"message": "Đã thêm sản phẩm vào giỏ hàng"}
