from passlib.context import CryptContext
from typing import Annotated
from sqlmodel import Session, select
from api.db.session import get_session
from fastapi import Depends, HTTPException, status
from api.user.scheme import Token, TokenData, RefreshTokenData
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timezone, timedelta
from api.user.utils import getUserFromDb
from api.auth.auth_utils import hash_password, verify_password, oauth_scheme
from api.auth.constants import SECRET_KEY, ALGOGRYTHYM, EXPIRE_TIME

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/token")

pwd_context = CryptContext(schemes="bcrypt")

def hash_password(password):
    return pwd_context.hash(password)

def verify_password(password, hash_password):
    return pwd_context.verify(password, hash_password)



def authenticate_user(username,
                      password,
                      session: Annotated[Session, Depends(get_session)]):
    db_user = getUserFromDb(session, username = username)
    if not db_user:
        return False
    if not verify_password(password = password, hash_password = db_user.password):
        return False
    return db_user

def create_access_token(data: dict, expiry_time:timedelta|None):
    data_to_encode = data.copy()
    if expiry_time:
        expiry = datetime.now(timezone.utc) + expiry_time
    else:
        expiry = datetime.now(timezone.utc) + timedelta(minutes=15)
    data_to_encode.update({"exp": expiry})
    encoded_jwt = jwt.encode(data_to_encode, SECRET_KEY, algorithm= ALGOGRYTHYM)
    return encoded_jwt



def create_refresh_token(data: dict, expiry_time:timedelta|None):
    data_to_encode = data.copy()
    if expiry_time:
        expiry = datetime.now(timezone.utc) + expiry_time
    else:
        expiry = datetime.now(timezone.utc) + timedelta(minutes=15)
    data_to_encode.update({"exp": expiry})
    encoded_jwt = jwt.encode(data_to_encode, SECRET_KEY, algorithm= ALGOGRYTHYM)
    return encoded_jwt

def validate_refresh_token(token: str,
                           session: Annotated[Session, Depends(get_session)]):
    # Import ở đây để tránh circular import
    from api.auth.token_blacklist import is_token_blacklisted
    
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token, Please login again",
        headers={"www-Authenticate": "Bearer"}
    )
    
    # Kiểm tra refresh token có trong blacklist không
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, ALGOGRYTHYM)
        email: str | None = payload.get("sub")
        print(email)
        if email is None:
            raise credential_exception
        token_data = RefreshTokenData(email=email)

    except:
        raise JWTError
    user = getUserFromDb(session, email = token_data.email)
    if not user:
        raise credential_exception
    return user