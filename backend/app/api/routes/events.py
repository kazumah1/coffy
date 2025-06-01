from fastapi import APIRouter, Depends, HTTPException
from app.models.event import Event
from app.services.database_service import DatabaseService
from app.dependencies import get_database_service
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=Event)
async def create_event(
    event: Event,
    db: DatabaseService = Depends(get_database_service),
):
    """Create a new event directly through the API.
    This endpoint is for direct event creation, distinct from the AI-assisted creation flow.
    """
    # Ensure timestamps are set
    now = datetime.now()
    payload = event.dict()
    payload["created_at"] = now.isoformat()
    payload["updated_at"] = now.isoformat()
    
    # Set status to 'confirmed' for direct creation
    payload["status"] = "confirmed"
    
    resp = db.client.table("events").insert(payload).execute()
    if resp.error:
        raise HTTPException(500, resp.error.message)
    return resp.data[0]

@router.get("/{event_id}", response_model=Event)
async def get_event(
    event_id: str,
    db: DatabaseService = Depends(get_database_service),
):
    """Get an event by ID."""
    event = await db.get_event_by_id(event_id)
    if not event:
        raise HTTPException(404, "Event not found")
    return event
