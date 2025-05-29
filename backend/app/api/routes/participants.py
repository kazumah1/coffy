from fastapi import APIRouter, Depends, HTTPException
from app.models.event_participant import EventParticipant
from services.database_service import DatabaseService
from dependencies import get_database_service

router = APIRouter()

@router.post("/", response_model=EventParticipant)
async def create_participant(
    participant: EventParticipant,
    db: DatabaseService = Depends(get_database_service),
):
    resp = db.client.table("event_participants").insert(participant.dict()).execute()
    if resp.error:
        raise HTTPException(500, resp.error.message)
    return resp.data[0]
