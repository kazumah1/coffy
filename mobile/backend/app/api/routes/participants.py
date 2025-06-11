from fastapi import APIRouter, Depends, HTTPException
from app.models.event_participant import EventParticipant
from app.services.database_service import DatabaseService
from app.dependencies import get_database_service

router = APIRouter()

@router.post("/", response_model=EventParticipant)
async def create_participant(
    participant: EventParticipant,
    db: DatabaseService = Depends(get_database_service),
):
    """Create a new event participant directly through the API.
    This endpoint is for direct participant creation, distinct from the AI-assisted creation flow.
    """
    # Set status to 'confirmed' for direct creation
    payload = participant.dict()
    payload["status"] = "confirmed"
    
    resp = db.client.table("event_participants").insert(payload).execute()
    if resp.error:
        raise HTTPException(500, resp.error.message)
    return resp.data[0]

@router.get("/event/{event_id}")
async def get_event_participants(
    event_id: str,
    db: DatabaseService = Depends(get_database_service),
):
    """Get all participants for a specific event."""
    participants = await db.get_event_participants(event_id)
    if not participants:
        return []
    return participants
