from services.database_service import DatabaseService
from services.google_oauth_service import GoogleOAuthHandler
from datetime import datetime, timedelta
from fastapi import HTTPException
from core.config import settings

class TokenManager:
    def __init__(self, database_service: DatabaseService, oauth_handler: GoogleOAuthHandler):
        self.database_service = database_service
        self.oauth_handler = oauth_handler

    def is_token_expired(self, expiry_time: datetime) -> bool:
        buffer_time = timedelta(minutes=5)
        return datetime.now() > (expiry_time - buffer_time)

    # def validate_token(self, token: str):
    #     try:
    #         payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    #         return payload
    #     except jwt.ExpiredSignatureError:
    #         raise HTTPException(status_code=401, detail="Token has expired")
    #     except jwt.InvalidTokenError:
    #         raise HTTPException(status_code=401, detail="Invalid token")

    async def store_token(self, user_id: str, access_token: str, refresh_token: str):
        response = await self.database_service.store_google_tokens(user_id, access_token, refresh_token, datetime.now() + timedelta(hours=1))
        if not response:
            raise Exception("Token not found")
        return response

    async def get_token(self, user_id: str):
        response = await self.database_service.get_google_tokens(user_id)
        if not response:
            raise Exception("Token not found")

        if self.is_token_expired(response['google_token_expiry']):
            print("Token expired, refreshing token")
            return await self.refresh_token(user_id, response['google_refresh_token'])
        return response
    
    async def refresh_token(self, user_id: str, refresh_token: str):
        try:
            credentials = await self.oauth_handler.refresh_token(refresh_token)
            await self.store_token(user_id, credentials.access_token, credentials.refresh_token)
            return credentials
        except Exception as e:
            raise HTTPException(status_code=401, detail="Failed to refresh token")
