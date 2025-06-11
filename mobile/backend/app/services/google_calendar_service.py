import requests
from datetime import datetime, timedelta
import icalendar
from typing import Optional
import aiohttp

class GoogleCalendarService:
    def __init__(self):
        self.base_url = "https://www.googleapis.com/calendar/v3"

    async def get_calendar_ids(self, access_token: str) -> list[str]:
        """Get list of calendar IDs for the user"""
        response = requests.get(
            f"{self.base_url}/users/me/calendarList",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return [calendar["id"] for calendar in response.json()["items"]]

    async def get_events(self, access_token: str, calendar_id: str, start_date: str, end_date: str) -> list[dict]:
        """Get events from a specific calendar"""
        # Ensure dates are in RFC3339 format with timezone
        try:
            # Add time component if only date is provided
            if len(start_date) == 10:  # YYYY-MM-DD format
                start_date = f"{start_date}T00:00:00+00:00"
            if len(end_date) == 10:  # YYYY-MM-DD format
                end_date = f"{end_date}T23:59:59+00:00"
                
        except ValueError as e:
            print(f"Error parsing dates: {e}")
            return []

        url = f"{self.base_url}/calendars/{calendar_id}/events"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "timeMin": start_date,
            "timeMax": end_date,
            "singleEvents": True,
            "orderBy": "startTime",
            "maxResults": 100  # Add a reasonable limit
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                return []
            
            response_json = response.json()
            events = response_json.get("items", [])
            
            formatted_events = []
            for event in events:
                if "start" not in event or "end" not in event:
                    continue
                    
                # Handle all-day events
                if "date" in event["start"]:
                    start_time = f"{event['start']['date']}T00:00:00+00:00"
                    end_time = f"{event['end']['date']}T23:59:59+00:00"
                else:
                    start_time = event["start"]["dateTime"]
                    end_time = event["end"]["dateTime"]
                
                formatted_events.append({
                    "summary": event.get("summary", "(No Title)"),
                    "start": start_time,
                    "end": end_time
                })
            
            print(f"Formatted events: {formatted_events}")
            return formatted_events
            
        except Exception as e:
            print(f"Error fetching events: {str(e)}")
            return []

    async def get_all_events(self, access_token: str, start_date: str = None, end_date: str = None) -> list[dict]:
        """Get events from all calendars"""
        # If no dates provided, use next 7 days
        if not start_date:
            start_date = datetime.now().isoformat()
        if not end_date:
            end_date = (datetime.now() + timedelta(days=7)).isoformat()
            
        calendar_ids = await self.get_calendar_ids(access_token)
        all_events = []
        for cal_id in calendar_ids:
            if cal_id == "en.usa#holiday@group.v.calendar.google.com":
                continue
            events = await self.get_events(access_token, cal_id, start_date, end_date)
            print(f"Found {len(events)} events for calendar {cal_id}")
            for event in events:
                event["calendar_id"] = cal_id
            all_events.extend(events)
        return all_events

    async def add_event(
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
        try:
            print("starting add_event")
            url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            print("continuing to add event")
            # Ensure timezone is properly formatted (replace Z with +00:00 if needed)
            if start["dateTime"].endswith("Z"):
                start["dateTime"] = start["dateTime"].replace("Z", "+00:00")
            if end["dateTime"].endswith("Z"):
                end["dateTime"] = end["dateTime"].replace("Z", "+00:00")
            print('continuing further')
            event_data = {
                "summary": title,
                "start": start,
                "end": end,
                "attendees": attendees
            }
            print("event_data", event_data)
            if location:
                event_data["location"] = location
            if description:
                event_data["description"] = description
            print("continuing to make request")
            async with aiohttp.ClientSession() as session:
                print("Making request to Google Calendar API...")
                async with session.post(url, headers=headers, json=event_data) as resp:
                    print(f"Response status: {resp.status}")
                    if resp.status != 200:
                        error_text = await resp.text()
                        print(f"Error response: {error_text}")
                        raise Exception(f"Failed to create event: {error_text}")
                    response_data = await resp.json()
                    print("Successfully created event")
                    return response_data
        except Exception as e:
            print(f"Error in add_event: {str(e)}")
            raise

    async def generate_ics(
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