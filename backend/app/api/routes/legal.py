from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from pathlib import Path

router = APIRouter()

# Get the path to the static directory relative to where the server is running
STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"

@router.get("/privacy-policy")
async def privacy_policy(request: Request):
    """Serve the privacy policy page."""
    # Check if the request is coming from non-www domain
    if not request.url.hostname.startswith('www.'):
        return RedirectResponse(
            url=f"https://www.coffy.app/privacy-policy",
            status_code=301
        )
    
    try:
        with open(STATIC_DIR / "privacy-policy.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Privacy policy page not found")

@router.get("/terms")
async def terms(request: Request):
    """Serve the terms and conditions page."""
    # Check if the request is coming from non-www domain
    if not request.url.hostname.startswith('www.'):
        return RedirectResponse(
            url=f"https://www.coffy.app/terms",
            status_code=301
        )
    
    try:
        with open(STATIC_DIR / "terms.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Terms page not found") 