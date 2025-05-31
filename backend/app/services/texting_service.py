import os
import requests
from typing import Optional
import aiohttp

class TextingService:
    def __init__(self):
        self.base_url = os.getenv("TEXTING_SERVICE_URL", "http://localhost:9090")

    async def send_message(self, to_number: str, message: str):
        """Send a text message to a phone number"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/text",
                data={
                    "number": to_number,
                    "message": message
                }
            ) as response:
                return await response.json()

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