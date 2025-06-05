from typing import Annotated
from sqlmodel import Session, select
from api.db.session import get_session
from api.user.model import User
from fastapi import Depends

def getUserFromDb(session: Annotated[Session, Depends(get_session)], username: str | None = None, email: str | None = None):
    if username:
        statement = select(User).where(User.username == username)
    elif email:
        statement = select(User).where(User.email == email)
    else:
        return None
    user = session.exec(statement).first()
    return user