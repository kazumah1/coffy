from fastapi import APIRouter, Depends
from app.services.database_service import DatabaseService
from app.services.google_calendar_service import GoogleCalendarService
from app.services.token_manager import TokenManager
from app.services.texting_service import TextingService
from app.services.openrouter_service import OpenRouterService
from app.dependencies import (
    get_database_service,
    get_google_calendar_service,
    get_token_manager,
    get_texting_service
)

router = APIRouter()

@router.get("/test")
async def test_user_retrieval(phone_number: str, id: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    # Start the agent loop in the background
    response =  await db_service.get_user_by_id(id)

    return response["name"]