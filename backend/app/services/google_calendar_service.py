import google.oauth2.credentials
import google_auth_oauthlib.flow
from typing import Optional
from urllib.parse import urlencode
from core.config import settings
import aiohttp
import requests

class GoogleCalendarService:
    def __init__(self):
        ...

    def get_calendar_ids(self, access_token: str) -> list[str]:
        ### Calls the Google Calendar API and returns calendars information ###
        response = requests.get("https://www.googleapis.com/calendar/v3/users/me/calendarList", headers={"Authorization": f"Bearer {access_token}"})
        return [calendar["id"] for calendar in response.json()["items"]]

    def get_freebusy(self, access_token: str, start_date: str, end_date: str) -> dict:
        ### Calls the Google Calendar API and returns freebusy information ###
        calendar_ids = self.get_calendar_ids(access_token)
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        body = {
            "timeMin": start_date,
            "timeMax": end_date,
            "items": calendar_ids
        }
        response = requests.post("https://www.googleapis.com/calendar/v3/freeBusy", headers=headers, json=body)
        return response.json()