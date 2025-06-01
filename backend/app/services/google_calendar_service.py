import requests
from datetime import datetime
import icalendar
from typing import Optional

class GoogleCalendarService:
    def __init__(self):
        self.base_url = "https://www.googleapis.com/calendar/v3"

    def get_calendar_ids(self, access_token: str) -> list[str]:
        """Get list of calendar IDs for the user"""
        response = requests.get(
            f"{self.base_url}/users/me/calendarList",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return [calendar["id"] for calendar in response.json()["items"]]

    def get_events(self, access_token: str, calendar_id: str, start_date: str, end_date: str) -> list[dict]:
        """Get events from a specific calendar"""
        url = f"{self.base_url}/calendars/{calendar_id}/events"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "timeMin": start_date,
            "timeMax": end_date,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return []
        events = response.json().get("items", [])
        return [
            {
                "summary": event.get("summary", "(No Title)"),
                "start": event["start"].get("dateTime", event["start"].get("date")),
                "end": event["end"].get("dateTime", event["end"].get("date"))
            }
            for event in events if "start" in event and "end" in event
        ]

    def get_all_events(self, access_token: str, start_date: str, end_date: str) -> list[dict]:
        """Get events from all calendars"""
        calendar_ids = self.get_calendar_ids(access_token)
        all_events = []
        for cal_id in calendar_ids:
            events = self.get_events(access_token, cal_id, start_date, end_date)
            for event in events:
                event["calendar_id"] = cal_id
            all_events.extend(events)
        return all_events

    def add_event(
        self,
        access_token: str,
        title: str,
        start: dict,
        end: dict,
        attendees: Optional[list[str]] = None,
        location: Optional[str] = None,
        description: Optional[str] = None
    ) -> dict:
        """Add an event to the user's primary calendar"""
        url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        event_data = {
            "summary": title,
            "start": start,
            "end": end,
            "attendees": attendees
        }
        
        if location:
            event_data["location"] = location
        if description:
            event_data["description"] = description
            
        response = requests.post(url, headers=headers, json=event_data)
        response.raise_for_status()
        return response.json()

    def generate_ics(
        self,
        title: str,
        start_time: str,
        end_time: str,
        location: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """Generate an ICS file content for an event"""
        cal = icalendar.Calendar()
        event = icalendar.Event()
        
        event.add('summary', title)
        event.add('dtstart', datetime.fromisoformat(start_time))
        event.add('dtend', datetime.fromisoformat(end_time))
        
        if location:
            event.add('location', location)
        if description:
            event.add('description', description)
            
        cal.add_component(event)
        return cal.to_ical().decode('utf-8')