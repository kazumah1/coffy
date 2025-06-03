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

        self.db_service = db_service
        self.openrouter_service = openrouter_service

    async def send_text( self, to_number: str, message: str, final: bool = False ) -> dict:

        url = "https://textbelt.com/text"
        if not final:
            payload = {
                "phone": to_number,
                "message": message,
                "replyWebhookUrl": "https://coffy.app/text/reply",
                "key": settings.TEXTING_API_KEY
            }
        else:
            payload = {
                "phone": to_number,
                "message": message,
                "key": settings.TEXTING_API_KEY
            }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as resp:
                return await resp.json()

    async def handle_text_reply(self, request: dict) -> dict:
        logger.info("Received SignalWire inbound SMS: %s", request)

        reply = request.get("Body", "") or request.get("text", "")
        from_number = request.get("From", "") or request.get("fromNumber", "")

        if self.db_service and self.openrouter_service:
            try:
                return await self.openrouter_service.handle_inbound_message(from_number, reply)
            except Exception as e:
                logger.error(f"Error in handle_text_reply → {e}")
                return {"message": reply, "from_number": from_number}

        # Fallback: just echo back
        return {"message": reply, "from_number": from_number}


    async def send_test_text(self, to_number: str, message: str) -> dict:
        url = "https://textbelt.com/text"
        payload = {
            "phone": to_number,
            "message": message,
            "key": settings.TEXTING_API_KEY + "_test"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as resp:
                return await resp.json()