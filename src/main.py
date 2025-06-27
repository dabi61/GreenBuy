from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from api.events import router as event_router
from api.user import router as user_router
from contextlib import asynccontextmanager
from api.db.session import init_db, get_session
from api.auth.auth import authenticate_user, create_access_token, validate_refresh_token
from api.auth.constants import EXPIRE_TIME
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import Depends, HTTPException
from sqlmodel import Session
from datetime import timedelta
from api.user.scheme import Token, RefreshRequest
from api.auth.token_blacklist import add_token_to_blacklist
from api.auth.dependency import get_current_user
from api.user.model import User
from api.auth.cleanup_task import start_background_tasks
from api.user.protected_routing import router as user_protected_router
from api.user.admin_routing import router as admin_router
from api.user.social_routing import router as social_router
from api.chat.connection_manager import connection_manager
from api.address.routing import router as address_router
from api.shop.routing import router as shop_router
from api.category.routing import router as category_router
from api.sub_category.routing import router as sub_category_router
from api.product.routing import router as product_router
from api.cart.routing import router as cart_router
from api.order.routing import router as order_router
from api.attribute.routing import router as attribute_router
from api.chat.routing import router as chat_router
# Payment imports 
from api.payment.routing import router as payment_router  
from api.payment.model import Payment, PaymentMethod, RefundRequest  # Import để SQLModel biết về models
# Debug imports
from api.db.debug import router as debug_router
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@asynccontextmanager
async def lifespan( app:FastAPI):
    #before app startup up
    init_db()
    # Khởi động background tasks
    start_background_tasks()
    # Khởi động chat connection manager
    await connection_manager.start_background_tasks()
    yield
    #clean up
    await connection_manager.stop_background_tasks()

app = FastAPI(lifespan=lifespan,
            title="GreenBuy API",
            description="API cho hệ thống GreenBuy - ứng dụng thương mại điện tử",
            version="1.0.0",
            )
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.png")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.include_router(event_router, prefix='/api/events', tags=["Events"]) #/api/events
app.include_router(user_router, prefix='/api/user', tags=["Register"])
app.include_router(user_protected_router, prefix='/api/user', tags=["User"])
app.include_router(social_router, prefix='/api/user', tags=["Social"])
app.include_router(admin_router, prefix='/api/admin', tags=["Admin"])
app.include_router(address_router, prefix='/api/addresses', tags=["Address"])
app.include_router(shop_router, prefix='/api/shops', tags=["Shop"])
app.include_router(category_router, prefix='/api/category', tags=["Category"])
app.include_router(sub_category_router, prefix='/api/sub_category', tags=["SubCategory"])
app.include_router(product_router, prefix='/api/product', tags=["Product"])
app.include_router(cart_router, prefix='/api/cart', tags=["Cart"])
app.include_router(order_router, prefix='/api/order', tags=["Order"])
app.include_router(attribute_router, prefix='/api/attribute', tags=["Attribute"])
app.include_router(chat_router, prefix='/api/chat', tags=["Chat"])
app.include_router(payment_router, prefix='/api/payment', tags=["Payment"])
app.include_router(debug_router, prefix='/api/debug', tags=["Debug"])



@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

#login
@app.post("/token", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                session: Annotated[Session, Depends(get_session)]):
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    expiry_time = timedelta(minutes=EXPIRE_TIME)
    access_token = create_access_token({"sub": form_data.username}, expiry_time)

    refresh_expire_time = timedelta(days=7)
    refresh_token = create_access_token({"sub": user.email}, refresh_expire_time)

    return Token(access_token=access_token, token_type="bearer", refresh_token=refresh_token)

@app.post("/logout")
def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    token: Annotated[str, Depends(oauth2_scheme)]
):
    """
    Logout user bằng cách thêm token vào blacklist
    """
    # Thêm access token vào blacklist
    add_token_to_blacklist(token)
    
    return {"message": "Successfully logged out"}

@app.post("/logout-all")
def logout_all_devices(
    current_user: Annotated[User, Depends(get_current_user)],
    request: RefreshRequest,
    token: Annotated[str, Depends(oauth2_scheme)]
):
    """
    Logout khỏi tất cả devices bằng cách blacklist cả access và refresh token
    """
    # Thêm access token vào blacklist
    add_token_to_blacklist(token)
    
    # Thêm refresh token vào blacklist
    refresh_token = request.old_refresh_data
    if refresh_token:
        add_token_to_blacklist(refresh_token)
    
    return {"message": "Successfully logged out from all devices"}

@app.post("/token/refresh")
def refresh_token(request: RefreshRequest,
                  session: Annotated[Session, Depends(get_session)]):
    old_refresh_token = request.old_refresh_data
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token, Please login again",
        headers={"WWW-Authenticate": "Bearer"}
    )

    user = validate_refresh_token(old_refresh_token, session)
    if not user:
        raise credential_exception

    expire_time = timedelta(minutes=EXPIRE_TIME)
    access_token = create_access_token({"sub": user.username}, expire_time)
    refresh_expire_time = timedelta(days=7)
    refresh_token = create_access_token({"sub": user.email}, refresh_expire_time)

    return Token(access_token=access_token, token_type="bearer", refresh_token=refresh_token)
