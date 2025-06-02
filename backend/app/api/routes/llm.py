from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.services.openrouter_service import OpenRouterService
from app.services.database_service import DatabaseService
from app.services.google_calendar_service import GoogleCalendarService
from app.services.token_manager import TokenManager
from app.services.texting_service import TextingService
from app.services.websocket_service import active_connections
from app.dependencies import get_database_service, get_google_calendar_service, get_token_manager, get_texting_service
from typing import Dict
import asyncio
import json

router = APIRouter()



@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: str, 
    db_service: DatabaseService = Depends(get_database_service)
):
    try:
        # Accept the connection first
        await websocket.accept()
        
        # Then verify the user
        user = await db_service.get_user_by_id(user_id)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        active_connections[user_id] = websocket
        
        try:
            while True:
                # Keep the connection alive
                await websocket.receive_text()
        except WebSocketDisconnect:
            if user_id in active_connections:
                del active_connections[user_id]
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        if user_id in active_connections:
            del active_connections[user_id]
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

@router.post("/prompt")
async def run_llm(
    request: str,
    creator_id: str,
    db_service: DatabaseService = Depends(get_database_service),
    google_calendar_service: GoogleCalendarService = Depends(get_google_calendar_service),
    token_manager: TokenManager = Depends(get_token_manager),
    texting_service: TextingService = Depends(get_texting_service),
):
    # Start the agent loop in the background
    openrouter_service = OpenRouterService(
        db_service=db_service,
        google_calendar_service=google_calendar_service,
        token_manager=token_manager,
        texting_service=texting_service
    )
    
    # Start the agent loop in the background
    print("starting agent loop")
    # asyncio.create_task(openrouter_service.run_agent_loop(request, creator_id))
    
    # Return immediately with a hardcoded response
    return {
        "success": True,
        "response": {
            "content": "On it - scheduling it right now!"
        }
    }

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