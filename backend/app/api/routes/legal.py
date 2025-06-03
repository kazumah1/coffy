from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

@router.get("/privacy-policy")
async def privacy_policy():
    """Serve the privacy policy page."""
    return FileResponse("app/static/privacy-policy.html")

@router.get("/terms")
async def terms():
    """Serve the terms and conditions page."""
    return FileResponse("app/static/terms.html") 