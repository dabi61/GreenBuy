from pydantic import BaseModel, Field

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class TokenData(BaseModel):
    username: str

class RefreshTokenData(BaseModel):
    email: str

class RefreshRequest(BaseModel):
    old_refresh_data: str