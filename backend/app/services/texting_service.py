import os
import requests
from typing import Optional, Dict, Any
import aiohttp
import logging
from core.config import settings
from services.database_service import DatabaseService
import json
from services.tools import AVAILABLE_TOOLS, TOOL_NAME_TO_INDEX


logger = logging.getLogger(__name__)

class TextingService:
    def __init__(self, db_service: DatabaseService = None, openrouter_service: 'OpenRouterService' = None):
        self.base_url = "https://textbelt.com"
        self.api_key = settings.TEXTING_API_KEY
        self.db_service = db_service
        self.openrouter_service = openrouter_service

    async def send_text(self, to_number: str, message: str, type: str):
        """Send a text message to a phone number"""
        reply_webhook_url = "https://952d-47-229-38-79.ngrok-free.app/text/reply"
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/text",
                data={
                    "phone": to_number,
                    "message": message,
                    "replyWebhookUrl": reply_webhook_url,
                    "key": self.api_key
                }
            ) as response:
                return await response.json()
            
            
    async def handle_text_reply(self, request: dict):
        """Handle a text reply"""
        print("Received text reply:", request)
        reply = request["text"]
        from_number = request["fromNumber"]
        
        if self.db_service and self.openrouter_service:
            try:
                # Use the stored OpenRouterService instance
                return await self.openrouter_service.handle_inbound_message(from_number, reply)
            except Exception as e:
                logger.error(f"Error handling text reply: {str(e)}")
                return {"message": reply, "from_number": from_number}
        
        return {"message": reply, "from_number": from_number}

    async def send_mms(self, to_number: str, message: str, attachment_content: str, attachment_filename: str):
        """Send a multimedia message with an attachment"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/mms",
                data={
                    "number": to_number,
                    "message": message,
                    "attachment_content": attachment_content,
                    "attachment_filename": attachment_filename
                }
            ) as response:
                return await response.json()