import os
import requests
import json
from typing import Optional
from .tools import AVAILABLE_TOOLS
from services.database_service import DatabaseService

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "gpt-3.5-turbo:free"

SYSTEM_PROMPT = (
    """
You are a calendar assistant. Take the user's request and return ONLY valid JSON matching this schema:

{
  "event": {
    "title":        "string",
    "start_time":   "string in ISO 8601 format",
    "end_time":     "string in ISO 8601 format",
    "location":     "string or null"
  },
  "participants": [
    {
      "name":         "string",
      "email":        "string or null",
      "role":         "string"
    }
  ]
}

Respond with ONLY the JSON object, no additional text. Do NOT include any explanatory text.
"""
)

class OpenRouterService:
    def __init__(self, db_service: DatabaseService):
        self.api_url = API_URL
        self.model = MODEL
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set in environment")
        self._current_event_id: Optional[str] = None
        self.db_service = db_service

    @property
    def current_event_id(self) -> Optional[str]:
        """Get the ID of the event currently being worked on."""
        return self._current_event_id

    def set_current_event(self, event_id: str) -> None:
        """Set the ID of the event currently being worked on."""
        self._current_event_id = event_id

    def clear_current_event(self) -> None:
        """Clear the current event ID."""
        self._current_event_id = None

    def parse_calendar_request(self, prompt: str, tools: list[dict] = None) -> dict:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
        }
        if tools is not None:
            payload["tools"] = tools
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        response = requests.post(self.api_url, json=payload, headers=headers)
        if not response.ok:
            raise RuntimeError(f"OpenRouter error {response.status_code}: {response.text}")
        json_response = response.json()
        raw = json_response.get("choices", [{}])[0].get("message", {}).get("content")
        if not isinstance(raw, str):
            raise RuntimeError("unexpected response from OpenRouter")
        try:
            parsed = json.loads(raw)
        except Exception:
            raise RuntimeError(f"invalid JSON from llm:\n{raw}")
        return parsed 
    
    async def create_draft_event(
        self,
        creator_id: str,
        title: str,
        description: str = None
    ) -> dict:
        # Create a draft event that can be completed later
        event = await self.db_service.create_draft_event(creator_id, title, description)
        self.set_current_event(event["id"])
        return event

    async def create_event_participant(
        self,
        phone_number: str,
        name: str
    ) -> dict:
        # Create a participant for the current event
        if not self.current_event_id:
            raise RuntimeError("No current event set")
            
        return await self.db_service.create_event_participant(
            self.current_event_id,
            phone_number,
            name
        )

    # TODO: tool for getting all contacts

    # TODO: tool for getting availability through google calendar

    # TODO: tool for getting availability through texting

    # TODO: tool for seeing if users are registered to app (if not, do it through texting)

    # TODO: tool for sending texts

    # TODO: tool for receiving responses

    # TODO: tool for scheduling events (when event details are finalized)