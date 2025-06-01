from fastapi import APIRouter, Depends
from app.services.openrouter_service import OpenRouterService
from app.services.database_service import DatabaseService
from app.services.google_calendar_service import GoogleCalendarService
from app.services.token_manager import TokenManager
from app.services.texting_service import TextingService
from app.dependencies import get_database_service, get_google_calendar_service, get_token_manager, get_texting_service

router = APIRouter()

@router.post("/prompt")
async def run_llm(
    request: str,
    creator_id: str,
    db_service: DatabaseService = Depends(get_database_service),
    google_calendar_service: GoogleCalendarService = Depends(get_google_calendar_service),
    token_manager: TokenManager = Depends(get_token_manager),
    texting_service: TextingService = Depends(get_texting_service),
):
    openrouter_service = OpenRouterService(
        db_service=db_service,
        google_calendar_service=google_calendar_service,
        token_manager=token_manager,
        texting_service=texting_service
    )
    response = await openrouter_service.run_agent_loop(request, creator_id)
    return response

@router.post("/create_event")
async def create_event(
    title: str,
    description: str,
    creator_id: str,
    db_service: DatabaseService = Depends(get_database_service),
    google_calendar_service: GoogleCalendarService = Depends(get_google_calendar_service),
    token_manager: TokenManager = Depends(get_token_manager),
    texting_service: TextingService = Depends(get_texting_service),
):
    openrouter_service = OpenRouterService(
        db_service=db_service,
        google_calendar_service=google_calendar_service,
        token_manager=token_manager,
        texting_service=texting_service
    )
    response = await openrouter_service.create_draft_event(creator_id, title, description)
    return response