from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from pathlib import Path

router = APIRouter()

# Get the path to the static directory relative to where the server is running
STATIC_DIR = Path("static")

@router.get("/privacy-policy")
async def privacy_policy(request: Request):
    """Serve the privacy policy page."""
    # Check if the request is coming from non-www domain
    if not request.url.hostname.startswith('www.'):
        return RedirectResponse(
            url=f"https://www.coffy.app/privacy-policy",
            status_code=301
        )
    return RedirectResponse(url="/static/privacy-policy.html")

@router.get("/terms")
async def terms(request: Request):
    """Serve the terms and conditions page."""
    # Check if the request is coming from non-www domain
    if not request.url.hostname.startswith('www.'):
        return RedirectResponse(
            url=f"https://www.coffy.app/terms",
            status_code=301
        )
    return RedirectResponse(url="/static/terms.html") 