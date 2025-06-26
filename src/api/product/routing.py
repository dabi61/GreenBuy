import os
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlmodel import Session, select
from typing import List, Annotated, Optional
from .model import Product
from .scheme import ProductRead
from api.db.pagination import PaginatedResponse
from api.auth.dependency import get_current_user
from api.auth.permission import require_seller_or_approver, ensure_resource_access, require_approver
from api.auth.auth import get_session
from api.shop.model import Shop
from api.user.model import User
from api.attribute.model import Attribute
from pydantic import BaseModel
import uuid


router = APIRouter()

class ProductApprovalRequest(BaseModel):
    approved: bool
    approval_note: str = None

# 📄 Read all with pagination and filtering
@router.get("/", response_model=dict)
def get_products(
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    sub_category_id: Optional[int] = None,
    shop_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = "created_at",  # name, price, created_at
    sort_order: str = "desc",  # asc, desc
    approved_only: bool = True,
    session: Session = Depends(get_session)
):
    """
    Lấy danh sách sản phẩm với phân trang và filtering
    """
    from sqlmodel import or_, and_, func
    
    # Tạo base query
    query = select(Product)
    
    # Apply filters
    filters = []
    
    if approved_only:
        filters.append(Product.is_approved == True)
    
    if search:
        filters.append(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        )
    
    if sub_category_id:
        filters.append(Product.sub_category_id == sub_category_id)
    elif category_id:
        # Nếu có category_id, filter theo tất cả sub_category thuộc category đó
        from api.sub_category.model import SubCategory
        sub_categories = session.exec(
            select(SubCategory.id).where(SubCategory.category_id == category_id)
        ).all()
        if sub_categories:
            filters.append(Product.sub_category_id.in_(sub_categories))
    
    if shop_id:
        filters.append(Product.shop_id == shop_id)
    
    if min_price is not None:
        filters.append(Product.price >= min_price)
    
    if max_price is not None:
        filters.append(Product.price <= max_price)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Count total items
    count_query = select(func.count(Product.product_id))
    if filters:
        count_query = count_query.where(and_(*filters))
    total = session.exec(count_query).one()
    
    # Apply sorting
    if sort_by == "name":
        if sort_order == "desc":
            query = query.order_by(Product.name.desc())
        else:
            query = query.order_by(Product.name.asc())
    elif sort_by == "price":
        if sort_order == "desc":
            query = query.order_by(Product.price.desc())
        else:
            query = query.order_by(Product.price.asc())
    else:  # created_at
        if sort_order == "desc":
            query = query.order_by(Product.create_at.desc())
        else:
            query = query.order_by(Product.create_at.asc())
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    products = session.exec(query).all()
    
    # Calculate pagination metadata
    total_pages = (total + limit - 1) // limit
    has_next = page < total_pages
    has_prev = page > 1
    
    # Convert products to dict to avoid model serialization issues
    items = []
    for product in products:
        items.append({
            "product_id": product.product_id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "cover": product.cover,
            "shop_id": product.shop_id,
            "sub_category_id": product.sub_category_id,
            "is_approved": product.is_approved,
            "create_at": product.create_at.isoformat() if product.create_at else None
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev
    }

# 📋 Get pending approval products (must be before /{product_id})
@router.get("/pending-approval", response_model=List[ProductRead])
def get_pending_products(
    current_user: Annotated[User, Depends(require_approver)],
    session: Session = Depends(get_session),
):
    """Lấy danh sách product chưa được approve (chỉ dành cho approver)"""
    products = session.exec(
        select(Product).where(Product.is_approved == None)
    ).all()
    return products

# 📈 Get trending products (must be before /{product_id})
@router.get("/trending", response_model=dict)
def get_trending_products(
    page: int = 1,
    limit: int = 10,
    session: Session = Depends(get_session)
):
    """
    Lấy sản phẩm trending (dựa trên ngày tạo gần đây)
    """
    from sqlmodel import func
    
    # Count total trending products
    count_query = select(func.count(Product.product_id)).where(Product.is_approved == True)
    total = session.exec(count_query).one()
    
    # Query products by latest created
    query = (
        select(Product)
        .where(Product.is_approved == True)
        .order_by(Product.create_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    
    products = session.exec(query).all()
    
    # Calculate pagination metadata
    total_pages = (total + limit - 1) // limit
    has_next = page < total_pages
    has_prev = page > 1
    
    # Convert to dict
    items = []
    for product in products:
        items.append({
            "product_id": product.product_id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "cover": product.cover,
            "shop_id": product.shop_id,
            "sub_category_id": product.sub_category_id,
            "create_at": product.create_at.isoformat() if product.create_at else None
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev
    }

# ⭐ Get featured products (must be before /{product_id})
@router.get("/featured", response_model=dict)
def get_featured_products(
    limit: int = 8,
    session: Session = Depends(get_session)
):
    """
    Lấy sản phẩm nổi bật cho homepage mobile
    """
    products = session.exec(
        select(Product)
        .where(Product.is_approved == True)
        .order_by(Product.create_at.desc())
        .limit(limit)
    ).all()
    
    # Convert to dict
    items = []
    for product in products:
        items.append({
            "product_id": product.product_id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "cover": product.cover,
            "shop_id": product.shop_id,
            "sub_category_id": product.sub_category_id,
            "create_at": product.create_at.isoformat() if product.create_at else None
        })
    
    return {
        "items": items,
        "count": len(items)
    }

# 🔍 Read by ID
@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=ProductRead)
async def create_product(
    current_user: Annotated[User, Depends(require_seller_or_approver)],
    session: Session = Depends(get_session),
    name: str = Form(...),
    description: str = Form(None),
    price: float = Form(None),
    sub_category_id: int = Form(...),
    cover: UploadFile = File(None),
):

    # Lấy shop từ user
    shop = session.exec(select(Shop).where(Shop.user_id == current_user.id)).first()
    if not shop:
        raise HTTPException(404, detail="No shop found")

    # Xử lý ảnh
    image_path = None
    if cover:
        ext = os.path.splitext(cover.filename)[1]
        filename = f"product_{uuid.uuid4().hex}{ext}"
        save_path = f"static/products/{filename}"

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(await cover.read())

        image_path = f"/static/products/{filename}"

    # Tạo product
    product = Product(
        name=name,
        description=description,
        price=price,
        sub_category_id=sub_category_id,
        shop_id=shop.id,
        cover=image_path,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
    name: str = Form(None),
    description: str = Form(None),
    price: float = Form(None),
    sub_category_id: int = Form(None),
    cover: UploadFile = File(None),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(404, detail="Product not found")

    # Kiểm tra quyền sở hữu qua shop
    shop = session.exec(select(Shop).where(Shop.id == product.shop_id)).first()
    if not shop:
        raise HTTPException(404, detail="Shop not found")
    
    # Kiểm tra user có quyền sửa product này không (owner hoặc approver)
    ensure_resource_access(current_user, shop.user_id, "product")

    # Cập nhật các trường
    if name is not None:
        product.name = name
    if description is not None:
        product.description = description
    if price is not None:
        product.price = price
    if sub_category_id is not None:
        product.sub_category_id = sub_category_id

    # Cập nhật ảnh nếu có
    if cover:
        ext = os.path.splitext(cover.filename)[1]
        filename = f"product_{uuid.uuid4().hex}{ext}"
        save_path = f"static/products/{filename}"

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(await cover.read())

        product.cover = f"/static/products/{filename}"

    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@router.patch("/{product_id}/approve", response_model=ProductRead)
def approve_product(
    product_id: int,
    approval_request: ProductApprovalRequest,
    current_user: Annotated[User, Depends(require_approver)],
    session: Session = Depends(get_session),
):
    """Approve hoặc reject product (chỉ dành cho approver)"""
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(404, detail="Product not found")

    # Cập nhật trạng thái approval
    product.is_approved = approval_request.approved
    product.approval_note = approval_request.approval_note
    product.approver_id = current_user.id

    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@router.get("/shop/{shop_id}", response_model=dict)
def get_products_by_shop(
    shop_id: int, 
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    sort_by: Optional[str] = "created_at",  # name, price, created_at
    sort_order: str = "desc",  # asc, desc
    approved_only: bool = True,
    session: Session = Depends(get_session)
):
    """
    Lấy danh sách sản phẩm theo shop với phân trang, filtering và search
    """
    from sqlmodel import and_, func, or_
    
    shop = session.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    # Tạo base query
    query = select(Product).where(Product.shop_id == shop_id)
    
    # Apply filters
    filters = [Product.shop_id == shop_id]
    
    if approved_only:
        filters.append(Product.is_approved == True)
    
    if search:
        filters.append(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        )
    
    if filters:
        query = query.where(and_(*filters))
    
    # Count total items
    count_query = select(func.count(Product.product_id))
    if filters:
        count_query = count_query.where(and_(*filters))
    total = session.exec(count_query).one()
    
    # Apply sorting
    if sort_by == "name":
        if sort_order == "desc":
            query = query.order_by(Product.name.desc())
        else:
            query = query.order_by(Product.name.asc())
    elif sort_by == "price":
        if sort_order == "desc":
            query = query.order_by(Product.price.desc())
        else:
            query = query.order_by(Product.price.asc())
    else:  # created_at
        if sort_order == "desc":
            query = query.order_by(Product.create_at.desc())
        else:
            query = query.order_by(Product.create_at.asc())
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    products = session.exec(query).all()
    
    # Calculate pagination metadata
    total_pages = (total + limit - 1) // limit
    has_next = page < total_pages
    has_prev = page > 1
    
    # Convert products to dict to match getproduct format
    items = []
    for product in products:
        items.append({
            "product_id": product.product_id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "cover": product.cover,
            "shop_id": product.shop_id,
            "sub_category_id": product.sub_category_id,
            "is_approved": product.is_approved,
            "create_at": product.create_at.isoformat() if product.create_at else None
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev
    }



@router.get("/categories/{category_id}/products", response_model=dict)
def get_products_by_category(
    category_id: int,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    session: Session = Depends(get_session)
):
    """
    Lấy sản phẩm theo category với phân trang (optimized cho mobile)
    """
    from api.sub_category.model import SubCategory
    from sqlmodel import and_, func
    
    # Get all subcategories in this category
    sub_categories = session.exec(
        select(SubCategory.id).where(SubCategory.category_id == category_id)
    ).all()
    
    if not sub_categories:
        raise HTTPException(status_code=404, detail="Category not found or has no products")
    
    # Count total products
    count_query = select(func.count(Product.product_id)).where(
        and_(
            Product.sub_category_id.in_(sub_categories),
            Product.is_approved == True
        )
    )
    total = session.exec(count_query).one()
    
    # Query products in these subcategories
    query = select(Product).where(
        and_(
            Product.sub_category_id.in_(sub_categories),
            Product.is_approved == True
        )
    )
    
    # Apply sorting
    if sort_by == "price":
        if sort_order == "desc":
            query = query.order_by(Product.price.desc())
        else:
            query = query.order_by(Product.price.asc())
    elif sort_by == "name":
        if sort_order == "desc":
            query = query.order_by(Product.name.desc())
        else:
            query = query.order_by(Product.name.asc())
    else:  # created_at
        if sort_order == "desc":
            query = query.order_by(Product.create_at.desc())
        else:
            query = query.order_by(Product.create_at.asc())
    
    # Apply pagination
    query = query.offset((page - 1) * limit).limit(limit)
    products = session.exec(query).all()
    
    # Calculate pagination metadata
    total_pages = (total + limit - 1) // limit
    has_next = page < total_pages
    has_prev = page > 1
    
    # Convert to dict
    items = []
    for product in products:
        items.append({
            "product_id": product.product_id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "cover": product.cover,
            "shop_id": product.shop_id,
            "sub_category_id": product.sub_category_id,
            "create_at": product.create_at.isoformat() if product.create_at else None
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev
    }