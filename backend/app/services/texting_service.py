import os
import requests

class TextingService:
    def __init__(self):
        ...

    def send_text(self, to_number: str, message: str):
        response = requests.post(
            "http://localhost:9090/text",
            data={
                "number": to_number,
                "message": message
            }
        )
        return response.json()