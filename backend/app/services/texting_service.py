import aiohttp
import logging
from typing import Optional

from app.core.config import settings
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class TextingService:
    def __init__(
        self,
        db_service: DatabaseService = None,
        openrouter_service: "OpenRouterService" = None
    ):
        # SignalWire configuration
        self.space_url = "coffy.signalwire.com"
        self.project_id = "a31d9015-86f4-4545-a078-f2a1a357e683"
        self.api_token = "PSK_ahnxKGbQggU1AovvoeHMJ3Ai"
        self.from_number = "INSERT LATER"  # e.g. "+1XXXYYYZZZZ"

        self.db_service = db_service
        self.openrouter_service = openrouter_service

    async def send_text( self, to_number: str, message: str, final: bool = False ) -> dict:
        url = (
            f"https://{self.space_url}"
            f"/api/laml/2010-04-01/Accounts/{self.project_id}/Messages.json"
        )

        # Basic auth with Project ID and API token
        auth = aiohttp.BasicAuth(self.project_id, self.api_token)

        payload = {
            "From": self.from_number,
            "To": to_number,
            "Body": message
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload, auth=auth) as resp:
                return await resp.json()


    async def send_mms(
        self,
        to_number: str,
        message: str,
        media_url: str,
    ) -> dict:
        url = (
            f"https://{self.space_url}"
            f"/api/laml/2010-04-01/Accounts/{self.project_id}/Messages.json"
        )
        auth = aiohttp.BasicAuth(self.project_id, self.api_token)

        payload = {
            "From": self.from_number,
            "To": to_number,
            "Body": message,
            "MediaUrl": media_url
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload, auth=auth) as resp:
                return await resp.json()


    async def handle_text_reply(self, request: dict) -> dict:
        logger.info("Received SignalWire inbound SMS: %s", request)

        reply = request.get("Body", "")
        from_number = request.get("From", "")

        if self.db_service and self.openrouter_service:
            try:
                return await self.openrouter_service.handle_inbound_message(from_number, reply)
            except Exception as e:
                logger.error(f"Error in handle_text_reply → {e}")
                return {"message": reply, "from_number": from_number}

        # Fallback: just echo back
        return {"message": reply, "from_number": from_number}


    async def send_test_text(self, to_number: str, message: str) -> dict:
        pass