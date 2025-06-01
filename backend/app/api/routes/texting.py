from fastapi import APIRouter, Depends
from app.services.texting_service import TextingService
from app.dependencies import get_texting_service
from app.models.conversation import Message

router = APIRouter()

@router.post("/")
async def send_text(message: Message, texting_service: TextingService = Depends(get_texting_service)):
    m = "can you confirm? - Coffee with Kaz by Coffy"
    n = "6265905589"
    return await texting_service.send_text(n, m, "confirmation")

@router.post("/reply")
async def handle_text_reply(request: dict, texting_service: TextingService = Depends(get_texting_service)):
    return await texting_service.handle_text_reply(request)