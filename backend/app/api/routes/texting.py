from fastapi import APIRouter, Depends
from services.texting_service import TextingService
from dependencies import get_texting_service
from models.conversation import Message

router = APIRouter()

@router.post("/text")
async def send_text(message: Message, texting_service: TextingService = Depends(get_texting_service)):
    return texting_service.send_text(message.to_number, message.content)