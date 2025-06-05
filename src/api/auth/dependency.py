from typing import Annotated
from sqlmodel import Session, select
from api.db.session import get_session
from fastapi import Depends, HTTPException, status
from api.user.model import User, Token, TokenData
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timezone, timedelta
from api.auth.auth_utils import oauth_scheme
from api.user.utils import getUserFromDb
from api.auth.auth import SECRET_KEY, ALGOGRYTHYM

def get_current_user (token: Annotated[str, Depends(oauth_scheme)],
                  session: Annotated[Session, Depends(get_session)]):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token, Please login again",
        headers={"www-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, ALGOGRYTHYM)
        username: str | None = payload.get("sub")
        if username is None:
            raise credential_exception
        token_data = TokenData(username=username)

    except:
        raise JWTError
    user = getUserFromDb(session, username = token_data.username)
    if not user:
        raise credential_exception
    return user