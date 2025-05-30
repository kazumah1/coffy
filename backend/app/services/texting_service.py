import os
import requests
from typing import Optional

class TextingService:
    def __init__(self):
        self.base_url = os.getenv("TEXTING_SERVICE_URL", "http://localhost:9090")

    def send_text(self, to_number: str, message: str):
        """Legacy method - use send_message instead"""
        return self.send_message(to_number, message)

    def send_message(self, to_number: str, message: str):
        """Send a text message to a phone number"""
        response = requests.post(
            f"{self.base_url}/text",
            data={
                "number": to_number,
                "message": message
            }
        )
        return response.json()

    def send_mms(self, to_number: str, message: str, attachment_content: str, attachment_filename: str):
        """Send a multimedia message with an attachment"""
        response = requests.post(
            f"{self.base_url}/mms",
            data={
                "number": to_number,
                "message": message,
                "attachment_content": attachment_content,
                "attachment_filename": attachment_filename
            }
        )
        return response.json()