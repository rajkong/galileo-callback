from pydantic import BaseModel
from datetime import datetime


class AccessTokenData(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
    timestamp: datetime

# Pydantic model for token data
class TokenData(BaseModel):
    code: str
    access_token: AccessTokenData|None = None

