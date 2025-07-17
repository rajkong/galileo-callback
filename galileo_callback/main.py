from datetime import datetime
import time

from fastapi import FastAPI, Query, HTTPException
import httpx
import os
from dotenv import load_dotenv

from galileo_callback.model import TokenData, AccessTokenData, RefreshTokenRequest

load_dotenv()

app = FastAPI()

# Box API configuration - these should be set as environment variables
BOX_CLIENT_ID = os.getenv("BOX_CLIENT_ID")
BOX_CLIENT_SECRET = os.getenv("BOX_CLIENT_SECRET")
BOX_REDIRECT_URI = os.getenv("BOX_REDIRECT_URI", "http://localhost:3227/callback")

# Global dictionary to store tokens with code as key
_token_store: dict[str, TokenData] = {}

@app.get("/")
async def hello_world():
    return {"message": "Hello World"}

@app.get("/callback")
async def callback(
    state: str = Query(...), 
    code: str = Query(...), 
    error: str = Query(None)
):
    if error:
        return {
            "message": "Authentication failed",
            "error": error,
            "state": state
        }

    _token_store[state] = TokenData(
        code=code,
    )
    return {
        "message": "Code received successfully",
        "state": state
    }

@app.get("/box/token")
async def get_token(key: str = Query(...)):
    """
    Retrieve token data by access code (authorization code)
    """
    if key not in _token_store:
        raise HTTPException(
            status_code=404,
            detail=f"No token found for key: {key}"
        )
    
    token_data = _token_store[key]
    token_data = await _get_access_token(token_data)

    return token_data.model_dump(mode="json")

@app.post("/box/refresh_token")
async def refresh_box_token(request: RefreshTokenRequest):
    """
    Refresh an access token using a refresh token
    """
    # Check if required Box API credentials are configured
    global BOX_CLIENT_ID, BOX_CLIENT_SECRET
    if not BOX_CLIENT_ID or not BOX_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Box API credentials not configured. Please set BOX_CLIENT_ID and BOX_CLIENT_SECRET environment variables."
        )

    if request.client_id != BOX_CLIENT_ID:
        raise HTTPException(
            status_code=400,
            detail="Invalid client ID"
        )

    if not request.refresh_token:
        raise HTTPException(
            status_code=400,
            detail="Missing refresh token"
        )
    
    # Use the refresh token to get a new access token
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://api.box.com/oauth2/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": request.refresh_token,
                    "client_id": BOX_CLIENT_ID,
                    "client_secret": BOX_CLIENT_SECRET
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )

            if token_response.status_code == 200:
                access_token_resp = token_response.json()
                access_token_data = AccessTokenData(
                    access_token=access_token_resp.get("access_token"),
                    refresh_token=access_token_resp.get("refresh_token"),
                    expires_in=access_token_resp.get("expires_in"),
                    token_type=access_token_resp.get("token_type"),
                    expires_at_time_seconds=time.time() + access_token_resp.get("expires_in")
                )
                return access_token_data.model_dump(mode="json")
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Token refresh failed: {token_response.text}"
                )

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to Box API: {str(e)}"
        )


async def _get_access_token(token_data: TokenData)-> TokenData:
    """
    Retrieve access token data by access code (authorization code)
    """
    # Check if required Box API credentials are configured
    global BOX_CLIENT_ID, BOX_CLIENT_SECRET
    if not BOX_CLIENT_ID or not BOX_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Box API credentials not configured. Please set BOX_CLIENT_ID and BOX_CLIENT_SECRET environment variables."
        )
    code = token_data.code
    # Exchange authorization code for access token
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://api.box.com/oauth2/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": BOX_CLIENT_ID,
                    "client_secret": BOX_CLIENT_SECRET,
                    "redirect_uri": BOX_REDIRECT_URI
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )

            if token_response.status_code == 200:
                access_token_resp = token_response.json()
                access_token_data = AccessTokenData(
                    access_token=access_token_resp.get("access_token"),
                    refresh_token=access_token_resp.get("refresh_token"),
                    expires_in=access_token_resp.get("expires_in"),
                    token_type=access_token_resp.get("token_type"),
                    expires_at_time_seconds=time.time()  + access_token_resp.get("expires_in")
                )
                token_data.token = access_token_data
                return token_data
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Token exchange failed: {token_response.text}"
                )

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to Box API: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3227)
