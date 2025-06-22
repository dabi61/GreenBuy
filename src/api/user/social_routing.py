from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func, and_, or_
from typing import List, Annotated
from datetime import datetime

from api.auth.dependency import get_current_user
from api.auth.auth import get_session
from .model import (
    User, UserFollow, ShopFollow, UserRating, ShopRating,
    FollowUserRequest, FollowShopRequest, RateUserRequest, RateShopRequest,
    UserFollowResponse, ShopFollowResponse, UserRatingResponse, ShopRatingResponse,
    FollowStatsResponse, RatingStatsResponse
)
from api.shop.model import Shop

router = APIRouter()

# ============================
# FOLLOW ENDPOINTS
# ============================

@router.post("/follow/user", response_model=UserFollowResponse)
def follow_user(
    request: FollowUserRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """Theo dõi một user khác"""
    
    # Không thể follow chính mình
    if current_user.id == request.following_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể theo dõi chính mình"
        )
    
    # Kiểm tra user được follow có tồn tại không
    target_user = session.get(User, request.following_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Người dùng không tồn tại"
        )
    
    # Kiểm tra đã follow chưa
    existing_follow = session.exec(
        select(UserFollow).where(
            and_(
                UserFollow.follower_id == current_user.id,
                UserFollow.following_id == request.following_id
            )
        )
    ).first()
    
    if existing_follow:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Đã theo dõi người dùng này rồi"
        )
    
    # Tạo follow mới
    new_follow = UserFollow(
        follower_id=current_user.id,
        following_id=request.following_id
    )
    session.add(new_follow)
    session.commit()
    session.refresh(new_follow)
    
    return UserFollowResponse(
        id=new_follow.id,
        follower_id=new_follow.follower_id,
        following_id=new_follow.following_id,
        created_at=new_follow.created_at,
        follower_username=current_user.username,
        following_username=target_user.username
    )

@router.delete("/follow/user/{following_id}")
def unfollow_user(
    following_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """Bỏ theo dõi user"""
    
    follow = session.exec(
        select(UserFollow).where(
            and_(
                UserFollow.follower_id == current_user.id,
                UserFollow.following_id == following_id
            )
        )
    ).first()
    
    if not follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy mối quan hệ theo dõi"
        )
    
    session.delete(follow)
    session.commit()
    
    return {"message": "Đã bỏ theo dõi thành công"}

@router.post("/follow/shop", response_model=ShopFollowResponse)
def follow_shop(
    request: FollowShopRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """Theo dõi một shop"""
    
    # Kiểm tra shop có tồn tại không
    shop = session.get(Shop, request.shop_id)
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop không tồn tại"
        )
    
    # Kiểm tra đã follow chưa
    existing_follow = session.exec(
        select(ShopFollow).where(
            and_(
                ShopFollow.user_id == current_user.id,
                ShopFollow.shop_id == request.shop_id
            )
        )
    ).first()
    
    if existing_follow:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Đã theo dõi shop này rồi"
        )
    
    # Tạo follow mới
    new_follow = ShopFollow(
        user_id=current_user.id,
        shop_id=request.shop_id
    )
    session.add(new_follow)
    session.commit()
    session.refresh(new_follow)
    
    return ShopFollowResponse(
        id=new_follow.id,
        user_id=new_follow.user_id,
        shop_id=new_follow.shop_id,
        created_at=new_follow.created_at,
        shop_name=shop.name
    )

@router.delete("/follow/shop/{shop_id}")
def unfollow_shop(
    shop_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """Bỏ theo dõi shop"""
    
    follow = session.exec(
        select(ShopFollow).where(
            and_(
                ShopFollow.user_id == current_user.id,
                ShopFollow.shop_id == shop_id
            )
        )
    ).first()
    
    if not follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy mối quan hệ theo dõi"
        )
    
    session.delete(follow)
    session.commit()
    
    return {"message": "Đã bỏ theo dõi shop thành công"}

@router.get("/followers", response_model=List[UserFollowResponse])
def get_my_followers(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
    page: int = 1,
    limit: int = 20
):
    """Xem danh sách người theo dõi mình"""
    
    offset = (page - 1) * limit
    
    follows = session.exec(
        select(UserFollow, User)
        .join(User, UserFollow.follower_id == User.id)
        .where(UserFollow.following_id == current_user.id)
        .offset(offset)
        .limit(limit)
    ).all()
    
    result = []
    for follow, follower in follows:
        result.append(UserFollowResponse(
            id=follow.id,
            follower_id=follow.follower_id,
            following_id=follow.following_id,
            created_at=follow.created_at,
            follower_username=follower.username,
            following_username=current_user.username
        ))
    
    return result

@router.get("/following", response_model=List[UserFollowResponse])
def get_my_following(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
    page: int = 1,
    limit: int = 20
):
    """Xem danh sách người mình đang theo dõi"""
    
    offset = (page - 1) * limit
    
    follows = session.exec(
        select(UserFollow, User)
        .join(User, UserFollow.following_id == User.id)
        .where(UserFollow.follower_id == current_user.id)
        .offset(offset)
        .limit(limit)
    ).all()
    
    result = []
    for follow, following in follows:
        result.append(UserFollowResponse(
            id=follow.id,
            follower_id=follow.follower_id,
            following_id=follow.following_id,
            created_at=follow.created_at,
            follower_username=current_user.username,
            following_username=following.username
        ))
    
    return result

@router.get("/following/shops", response_model=List[ShopFollowResponse])
def get_my_shop_following(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
    page: int = 1,
    limit: int = 20
):
    """Xem danh sách shop mình đang theo dõi"""
    
    offset = (page - 1) * limit
    
    follows = session.exec(
        select(ShopFollow, Shop)
        .join(Shop, ShopFollow.shop_id == Shop.id)
        .where(ShopFollow.user_id == current_user.id)
        .offset(offset)
        .limit(limit)
    ).all()
    
    result = []
    for follow, shop in follows:
        result.append(ShopFollowResponse(
            id=follow.id,
            user_id=follow.user_id,
            shop_id=follow.shop_id,
            created_at=follow.created_at,
            shop_name=shop.name
        ))
    
    return result

@router.get("/followers/my-shop", response_model=List[dict])
def get_my_shop_followers(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
    page: int = 1,
    limit: int = 20
):
    """Xem danh sách người theo dõi shop của mình"""
    
    # Lấy shop của user hiện tại
    user_shop = session.exec(
        select(Shop).where(Shop.user_id == current_user.id)
    ).first()
    
    if not user_shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bạn chưa có shop nào"
        )
    
    offset = (page - 1) * limit
    
    # Lấy danh sách users đang follow shop của mình
    follows = session.exec(
        select(ShopFollow, User)
        .join(User, ShopFollow.user_id == User.id)
        .where(ShopFollow.shop_id == user_shop.id)
        .offset(offset)
        .limit(limit)
    ).all()
    
    result = []
    for follow, follower in follows:
        result.append({
            "follow_id": follow.id,
            "user_id": follower.id,
            "username": follower.username,
            "first_name": follower.first_name,
            "last_name": follower.last_name,
            "avatar": follower.avatar,
            "followed_at": follow.created_at.isoformat() if follow.created_at else None,
            "shop_id": user_shop.id,
            "shop_name": user_shop.name
        })
    
    return result

@router.get("/followers/shop/{shop_id}", response_model=List[dict])
def get_shop_followers(
    shop_id: int,
    session: Session = Depends(get_session),
    page: int = 1,
    limit: int = 20
):
    """Xem danh sách người theo dõi một shop cụ thể (public API)"""
    
    # Kiểm tra shop có tồn tại không
    shop = session.get(Shop, shop_id)
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop không tồn tại"
        )
    
    offset = (page - 1) * limit
    
    # Lấy danh sách users đang follow shop này
    follows = session.exec(
        select(ShopFollow, User)
        .join(User, ShopFollow.user_id == User.id)
        .where(ShopFollow.shop_id == shop_id)
        .order_by(ShopFollow.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    
    result = []
    for follow, follower in follows:
        result.append({
            "follow_id": follow.id,
            "user_id": follower.id,
            "username": follower.username,
            "first_name": follower.first_name,
            "last_name": follower.last_name,
            "avatar": follower.avatar,
            "followed_at": follow.created_at.isoformat() if follow.created_at else None,
            "shop_id": shop.id,
            "shop_name": shop.name
        })
    
    return result

@router.get("/follow/stats", response_model=FollowStatsResponse)
def get_follow_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """Thống kê follow của user hiện tại"""
    
    # Đếm followers
    followers_count = session.exec(
        select(func.count(UserFollow.id))
        .where(UserFollow.following_id == current_user.id)
    ).one()
    
    # Đếm following users
    following_count = session.exec(
        select(func.count(UserFollow.id))
        .where(UserFollow.follower_id == current_user.id)
    ).one()
    
    # Đếm following shops
    shop_following_count = session.exec(
        select(func.count(ShopFollow.id))
        .where(ShopFollow.user_id == current_user.id)
    ).one()
    
    # Đếm followers của shop mình (nếu có shop)
    my_shop_followers_count = 0
    user_shop = session.exec(
        select(Shop).where(Shop.user_id == current_user.id)
    ).first()
    
    if user_shop:
        my_shop_followers_count = session.exec(
            select(func.count(ShopFollow.id))
            .where(ShopFollow.shop_id == user_shop.id)
        ).one()
    
    return FollowStatsResponse(
        followers_count=followers_count,
        following_count=following_count,
        shop_following_count=shop_following_count,
        my_shop_followers_count=my_shop_followers_count
    )

# ============================
# RATING ENDPOINTS
# ============================

@router.post("/rating/user", response_model=UserRatingResponse)
def rate_user(
    request: RateUserRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """Đánh giá một user"""
    
    # Không thể đánh giá chính mình
    if current_user.id == request.rated_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể đánh giá chính mình"
        )
    
    # Kiểm tra user được đánh giá có tồn tại không
    target_user = session.get(User, request.rated_user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Người dùng không tồn tại"
        )
    
    # Kiểm tra đã đánh giá chưa
    existing_rating = session.exec(
        select(UserRating).where(
            and_(
                UserRating.rater_id == current_user.id,
                UserRating.rated_user_id == request.rated_user_id
            )
        )
    ).first()
    
    if existing_rating:
        # Cập nhật đánh giá hiện tại
        existing_rating.rating = request.rating
        existing_rating.comment = request.comment
        existing_rating.updated_at = datetime.utcnow()
        session.add(existing_rating)
        session.commit()
        session.refresh(existing_rating)
        
        return UserRatingResponse(
            id=existing_rating.id,
            rater_id=existing_rating.rater_id,
            rated_user_id=existing_rating.rated_user_id,
            rating=existing_rating.rating,
            comment=existing_rating.comment,
            created_at=existing_rating.created_at,
            updated_at=existing_rating.updated_at,
            rater_username=current_user.username,
            rated_user_username=target_user.username
        )
    
    # Tạo đánh giá mới
    new_rating = UserRating(
        rater_id=current_user.id,
        rated_user_id=request.rated_user_id,
        rating=request.rating,
        comment=request.comment
    )
    session.add(new_rating)
    session.commit()
    session.refresh(new_rating)
    
    return UserRatingResponse(
        id=new_rating.id,
        rater_id=new_rating.rater_id,
        rated_user_id=new_rating.rated_user_id,
        rating=new_rating.rating,
        comment=new_rating.comment,
        created_at=new_rating.created_at,
        updated_at=new_rating.updated_at,
        rater_username=current_user.username,
        rated_user_username=target_user.username
    )

@router.post("/rating/shop", response_model=ShopRatingResponse)
def rate_shop(
    request: RateShopRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """Đánh giá một shop"""
    
    # Kiểm tra shop có tồn tại không
    shop = session.get(Shop, request.shop_id)
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop không tồn tại"
        )
    
    # Kiểm tra đã đánh giá chưa
    existing_rating = session.exec(
        select(ShopRating).where(
            and_(
                ShopRating.user_id == current_user.id,
                ShopRating.shop_id == request.shop_id
            )
        )
    ).first()
    
    if existing_rating:
        # Cập nhật đánh giá hiện tại
        existing_rating.rating = request.rating
        existing_rating.comment = request.comment
        existing_rating.updated_at = datetime.utcnow()
        session.add(existing_rating)
        session.commit()
        session.refresh(existing_rating)
        
        return ShopRatingResponse(
            id=existing_rating.id,
            user_id=existing_rating.user_id,
            shop_id=existing_rating.shop_id,
            rating=existing_rating.rating,
            comment=existing_rating.comment,
            created_at=existing_rating.created_at,
            updated_at=existing_rating.updated_at,
            user_username=current_user.username,
            shop_name=shop.name
        )
    
    # Tạo đánh giá mới
    new_rating = ShopRating(
        user_id=current_user.id,
        shop_id=request.shop_id,
        rating=request.rating,
        comment=request.comment
    )
    session.add(new_rating)
    session.commit()
    session.refresh(new_rating)
    
    return ShopRatingResponse(
        id=new_rating.id,
        user_id=new_rating.user_id,
        shop_id=new_rating.shop_id,
        rating=new_rating.rating,
        comment=new_rating.comment,
        created_at=new_rating.created_at,
        updated_at=new_rating.updated_at,
        user_username=current_user.username,
        shop_name=shop.name
    )

@router.get("/rating/user/{user_id}", response_model=List[UserRatingResponse])
def get_user_ratings(
    user_id: int,
    session: Session = Depends(get_session),
    page: int = 1,
    limit: int = 20
):
    """Xem đánh giá của một user"""
    
    offset = (page - 1) * limit
    
    ratings = session.exec(
        select(UserRating, User.username.label("rater_username"))
        .join(User, UserRating.rater_id == User.id)
        .where(UserRating.rated_user_id == user_id)
        .offset(offset)
        .limit(limit)
    ).all()
    
    # Get rated user info
    rated_user = session.get(User, user_id)
    if not rated_user:
        raise HTTPException(status_code=404, detail="User không tồn tại")
    
    result = []
    for rating, rater_username in ratings:
        result.append(UserRatingResponse(
            id=rating.id,
            rater_id=rating.rater_id,
            rated_user_id=rating.rated_user_id,
            rating=rating.rating,
            comment=rating.comment,
            created_at=rating.created_at,
            updated_at=rating.updated_at,
            rater_username=rater_username,
            rated_user_username=rated_user.username
        ))
    
    return result

@router.get("/rating/shop/{shop_id}", response_model=List[ShopRatingResponse])
def get_shop_ratings(
    shop_id: int,
    session: Session = Depends(get_session),
    page: int = 1,
    limit: int = 20
):
    """Xem đánh giá của một shop"""
    
    offset = (page - 1) * limit
    
    ratings = session.exec(
        select(ShopRating, User, Shop)
        .join(User, ShopRating.user_id == User.id)
        .join(Shop, ShopRating.shop_id == Shop.id)
        .where(ShopRating.shop_id == shop_id)
        .offset(offset)
        .limit(limit)
    ).all()
    
    result = []
    for rating, user, shop in ratings:
        result.append(ShopRatingResponse(
            id=rating.id,
            user_id=rating.user_id,
            shop_id=rating.shop_id,
            rating=rating.rating,
            comment=rating.comment,
            created_at=rating.created_at,
            updated_at=rating.updated_at,
            user_username=user.username,
            shop_name=shop.name
        ))
    
    return result

@router.get("/rating/user/{user_id}/stats", response_model=RatingStatsResponse)
def get_user_rating_stats(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Thống kê đánh giá của user"""
    
    # Đếm tổng ratings
    total_ratings = session.exec(
        select(func.count(UserRating.id))
        .where(UserRating.rated_user_id == user_id)
    ).one()
    
    # Tính điểm trung bình
    avg_rating = session.exec(
        select(func.avg(UserRating.rating))
        .where(UserRating.rated_user_id == user_id)
    ).one() or 0.0
    
    # Phân tích theo từng điểm
    rating_breakdown = {}
    for i in range(1, 6):
        count = session.exec(
            select(func.count(UserRating.id))
            .where(and_(
                UserRating.rated_user_id == user_id,
                UserRating.rating == i
            ))
        ).one()
        rating_breakdown[str(i)] = count
    
    return RatingStatsResponse(
        total_ratings=total_ratings,
        average_rating=round(float(avg_rating), 2),
        rating_breakdown=rating_breakdown
    )

@router.get("/rating/shop/{shop_id}/stats", response_model=RatingStatsResponse)
def get_shop_rating_stats(
    shop_id: int,
    session: Session = Depends(get_session)
):
    """Thống kê đánh giá của shop"""
    
    # Đếm tổng ratings
    total_ratings = session.exec(
        select(func.count(ShopRating.id))
        .where(ShopRating.shop_id == shop_id)
    ).one()
    
    # Tính điểm trung bình
    avg_rating = session.exec(
        select(func.avg(ShopRating.rating))
        .where(ShopRating.shop_id == shop_id)
    ).one() or 0.0
    
    # Phân tích theo từng điểm
    rating_breakdown = {}
    for i in range(1, 6):
        count = session.exec(
            select(func.count(ShopRating.id))
            .where(and_(
                ShopRating.shop_id == shop_id,
                ShopRating.rating == i
            ))
        ).one()
        rating_breakdown[str(i)] = count
    
    return RatingStatsResponse(
        total_ratings=total_ratings,
        average_rating=round(float(avg_rating), 2),
        rating_breakdown=rating_breakdown
    ) 