from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional





class AccessTokenData(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
    expires_at_time_seconds: float


# Pydantic model for token data
class TokenData(BaseModel):
    code: str
    token: Optional[AccessTokenData] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str
    client_id: str
