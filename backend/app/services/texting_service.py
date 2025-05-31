import os
import requests
from typing import Optional
import aiohttp

class TextingService:
    def __init__(self):
        self.base_url = "https://textbelt.com"

    async def send_message(self, to_number: str, message: str):
        """Send a text message to a phone number"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://textbelt.com/text", 
                data={
                    "phone": to_number,
                    "message": message,
                    "replyWebhookUrl": "https://coffy.app/texting/reply",
                    "key": os.getenv("TEXTING_API_KEY")
                }
            ) as response:
                return await response.json()
            
    async def handle_text_reply(self, request: dict):
        """Handle a text reply"""
        print(request)
        reply = request["text"]
        from_number = request["fromNumber"]
        #return {"message": reply, "from_number": from_number}
        return {"message": "sure", "from_number": "6265905589"}

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