from fastapi import FastAPI, HTTPException, status
from api.events import router as event_router
from api.user import router as user_router
from contextlib import asynccontextmanager
from api.db.session import init_db, get_session
from api.auth.auth import authenticate_user, create_access_token, EXPIRE_TIME, validate_refresh_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import Depends, HTTPException
from sqlmodel import Session
from datetime import timedelta
from api.user.model import Token, RefreshRequest


from fastapi.middleware.cors import CORSMiddleware

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@asynccontextmanager
async def lifespan( app:FastAPI):
    #before app startup up
    init_db()
    yield
    #clean up

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <- sửa lại đúng chính tả
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(event_router, prefix='/api/events') #/api/events
app.include_router(user_router, prefix='/api/user', tags=["User"])


@app.get("/")
def read_root():
    return {"message": "Hello, world!"}


@app.get("/healthz")
def health_check():
    return {"status": "ok"}

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