from fastapi import FastAPI
from api.events import router as event_router
from api.user import router as user_router
from contextlib import asynccontextmanager
from api.db.session import init_db
from fastapi.security import OAuth2PasswordBearer

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
app.include_router(user_router, prefix='/api/user')


@app.get("/")
def read_root():
    return {"message": "Hello, world!"}


@app.get("/healthz")
def health_check():
    return {"status": "ok"}