from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from api.auth.dependency import get_current_user
from api.auth.auth import get_session
from api.user.model import User
from api.cart.model import Cart, CartItem
from api.product.model import Product
from api.shop.model import Shop
from api.attribute.model import Attribute
from api.cart.scheme import CartShopGroup, CartItemRead, UpdateCartItemQuantity, CartItemCreate, CartItemActionResponse

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
        attribute = session.get(Attribute, item.attribute_id)
        if not attribute:
            continue

        product = session.get(Product, attribute.product_id)
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
            attribute_id=attribute.attribute_id,
            quantity=item.quantity,
            product_id=product.product_id,
            product_name=product.name,
            price=attribute.price,
            cover=product.cover,
            color=attribute.color,
            size=attribute.size,
            attribute_image=attribute.image,
            available_quantity=attribute.quantity
        ))

    return list(shop_groups.values())


@router.delete("/shop/{shop_id}", response_model=dict)
def delete_items_by_shop(
    shop_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Xóa tất cả cart items từ một shop cụ thể"""
    cart = session.exec(select(Cart).where(Cart.user_id == current_user.id)).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    # Verify shop exists
    shop = session.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    # Sử dụng JOIN query để tối ưu hiệu suất
    deleted_items = session.exec(
        select(CartItem)
        .join(Attribute, CartItem.attribute_id == Attribute.attribute_id)
        .join(Product, Attribute.product_id == Product.product_id)
        .where(CartItem.cart_id == cart.id)
        .where(Product.shop_id == shop_id)
    ).all()

    if not deleted_items:
        raise HTTPException(status_code=404, detail="No items found for this shop in your cart")

    # Get details before deletion for response
    deleted_count = len(deleted_items)
    
    # Delete items
    for item in deleted_items:
        session.delete(item)
    session.commit()

    return {
        "message": f"Successfully deleted {deleted_count} item(s) from shop '{shop.name}'",
        "shop_id": shop_id,
        "shop_name": shop.name,
        "deleted_count": deleted_count
    }


@router.delete("/attribute/{attribute_id}", response_model=CartItemActionResponse)
def delete_cart_item(
    attribute_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Xóa một attribute cụ thể khỏi giỏ hàng"""
    cart = session.exec(select(Cart).where(Cart.user_id == current_user.id)).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    # Verify attribute exists
    attribute = session.get(Attribute, attribute_id)
    if not attribute:
        raise HTTPException(status_code=404, detail="Attribute not found")

    # Find cart item
    item = session.exec(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.attribute_id == attribute_id
        )
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found in your cart")

    # Store quantity before deletion
    deleted_quantity = item.quantity

    # Delete item
    session.delete(item)
    session.commit()

    return CartItemActionResponse(
        message=f"Successfully removed item from cart (quantity: {deleted_quantity})",
        attribute_id=attribute_id,
        quantity=0  # 0 indicates item was removed
    )


@router.put("/attribute/{attribute_id}", response_model=CartItemActionResponse)
def update_cart_item_quantity(
    attribute_id: int,
    update_data: UpdateCartItemQuantity,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Cập nhật số lượng của một attribute trong giỏ hàng"""
    cart = session.exec(select(Cart).where(Cart.user_id == current_user.id)).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    # Verify attribute exists and get stock info
    attribute = session.get(Attribute, attribute_id)
    if not attribute:
        raise HTTPException(status_code=404, detail="Attribute not found")

    # Find cart item
    item = session.exec(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.attribute_id == attribute_id
        )
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found in your cart")

    # Validate quantity
    if update_data.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")

    if update_data.quantity > attribute.quantity:
        raise HTTPException(
            status_code=400, 
            detail=f"Requested quantity ({update_data.quantity}) exceeds available stock ({attribute.quantity})"
        )

    # Store old quantity for comparison
    old_quantity = item.quantity

    # Update quantity
    item.quantity = update_data.quantity
    session.add(item)
    session.commit()
    session.refresh(item)

    # Determine action message
    if update_data.quantity > old_quantity:
        action = "increased"
    elif update_data.quantity < old_quantity:
        action = "decreased"
    else:
        action = "unchanged"

    return CartItemActionResponse(
        message=f"Cart item quantity {action} from {old_quantity} to {update_data.quantity}",
        attribute_id=attribute_id,
        quantity=item.quantity
    )


@router.post("/add", summary="Thêm attribute vào giỏ hàng")
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

    # Kiểm tra attribute có tồn tại không
    attribute = session.exec(select(Attribute).where(Attribute.attribute_id == item.attribute_id)).first()
    if not attribute:
        raise HTTPException(status_code=404, detail="Attribute không tồn tại")

    # Kiểm tra số lượng có sẵn
    if item.quantity > attribute.quantity:
        raise HTTPException(
            status_code=400, 
            detail=f"Số lượng yêu cầu ({item.quantity}) vượt quá tồn kho ({attribute.quantity})"
        )

    # Kiểm tra xem attribute đã có trong giỏ chưa (theo cart_id và attribute_id)
    existing_item = session.exec(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.attribute_id == item.attribute_id
        )
    ).first()

    if existing_item:
        new_quantity = existing_item.quantity + item.quantity
        if new_quantity > attribute.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Tổng số lượng ({new_quantity}) vượt quá tồn kho ({attribute.quantity})"
            )
        existing_item.quantity = new_quantity
        session.add(existing_item)
    else:
        new_item = CartItem(
            cart_id=cart.id,
            attribute_id=item.attribute_id,
            quantity=item.quantity
        )
        session.add(new_item)

    session.commit()
    return {"message": "Đã thêm attribute vào giỏ hàng"}


@router.delete("/product/{product_id}", response_model=dict)
def delete_items_by_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Xóa tất cả cart items của một product (tất cả attributes)"""
    cart = session.exec(select(Cart).where(Cart.user_id == current_user.id)).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    # Verify product exists
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Sử dụng JOIN query để tối ưu hiệu suất
    deleted_items = session.exec(
        select(CartItem)
        .join(Attribute, CartItem.attribute_id == Attribute.attribute_id)
        .where(CartItem.cart_id == cart.id)
        .where(Attribute.product_id == product_id)
    ).all()

    if not deleted_items:
        raise HTTPException(status_code=404, detail="No items found for this product in your cart")

    # Get details before deletion
    deleted_count = len(deleted_items)
    
    # Delete items
    for item in deleted_items:
        session.delete(item)
    session.commit()

    return {
        "message": f"Successfully deleted {deleted_count} variant(s) of product '{product.name}'",
        "product_id": product_id,
        "product_name": product.name,
        "deleted_count": deleted_count
    }


@router.delete("/clear", response_model=dict)
def clear_cart(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Xóa toàn bộ giỏ hàng"""
    cart = session.exec(select(Cart).where(Cart.user_id == current_user.id)).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    # Get all items to count
    all_items = session.exec(
        select(CartItem).where(CartItem.cart_id == cart.id)
    ).all()

    if not all_items:
        return {
            "message": "Cart is already empty",
            "deleted_count": 0
        }

    deleted_count = len(all_items)
    
    # Delete all items
    for item in all_items:
        session.delete(item)
    session.commit()

    return {
        "message": f"Successfully cleared cart ({deleted_count} item(s) removed)",
        "deleted_count": deleted_count
    }
