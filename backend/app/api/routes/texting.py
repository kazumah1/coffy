from fastapi import APIRouter, Depends
from services.texting_service import TextingService
from dependencies import get_texting_service
from models.conversation import Message

router = APIRouter()

@router.post("/text")
async def send_text(message: Message, texting_service: TextingService = Depends(get_texting_service)):
    return await texting_service.send_message(message.to_number, message.content)

@router.post("/text/reply")
async def handle_text_reply(request: dict, texting_service: TextingService = Depends(get_texting_service)):
    return await texting_service.handle_text_reply(request)