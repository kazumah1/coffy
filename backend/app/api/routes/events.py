from fastapi import APIRouter, Depends, HTTPException
from models.event import Event
from services.database_service import DatabaseService
from dependencies import get_database_service

router = APIRouter()

@router.post("/", response_model=Event)
async def create_event(
    event: Event,
    db: DatabaseService = Depends(get_database_service),
):
    #convert datetimes to ISO strings
    payload = event.dict()
    payload["created_at"] = payload["created_at"].isoformat()
    payload["updated_at"] = payload["updated_at"].isoformat()
    resp = db.client.table("events").insert(payload).execute()
    if resp.error:
        raise HTTPException(500, resp.error.message)
    return resp.data[0]
