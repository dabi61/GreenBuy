from typing import Annotated
from sqlmodel import Session
from api.db.session import get_session
from fastapi import Depends, HTTPException, status
from api.auth.scheme import TokenData
from jose import jwt, JWTError, ExpiredSignatureError
from api.auth.auth_utils import oauth_scheme
from api.user.utils import getUserFromDb
from api.auth.constants import SECRET_KEY, ALGOGRYTHYM
from api.auth.token_blacklist import is_token_blacklisted

def get_current_user(
    token: Annotated[str, Depends(oauth_scheme)],
    session: Annotated[Session, Depends(get_session)]
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Kiểm tra token có trong blacklist không (đã logout)
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGOGRYTHYM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception

    user = getUserFromDb(session, token_data.username)
    if not user:
        raise credentials_exception

    return user