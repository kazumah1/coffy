import requests
from datetime import datetime

class GoogleCalendarService:
    def __init__(self):
        ...

    def get_calendar_ids(self, access_token: str) -> list[str]:
        ### Calls the Google Calendar API and returns calendars information ###
        response = requests.get("https://www.googleapis.com/calendar/v3/users/me/calendarList", headers={"Authorization": f"Bearer {access_token}"})
        return [calendar["id"] for calendar in response.json()["items"]]

    def get_events(self, access_token: str, calendar_id: str, start_date: str, end_date: str) -> list[dict]:
        # Calls the Google Calendar Events List API and returns events with names and times
        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
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
        # Only keep events that have start and end times
        return [
            {
                "summary": event.get("summary", "(No Title)"),
                "start": event["start"].get("dateTime", event["start"].get("date")),
                "end": event["end"].get("dateTime", event["end"].get("date"))
            }
            for event in events if "start" in event and "end" in event
        ]

    def get_all_events(self, access_token: str, start_date: str, end_date: str) -> list[dict]:
        # Aggregates events from all calendars
        calendar_ids = self.get_calendar_ids(access_token)
        all_events = []
        for cal_id in calendar_ids:
            events = self.get_events(access_token, cal_id, start_date, end_date)
            for event in events:
                event["calendar_id"] = cal_id
            all_events.extend(events)
        return all_events