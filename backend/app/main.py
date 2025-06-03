from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from app.api.routes import auth
from app.api.routes.events import router as events_router
from app.api.routes.participants import router as participants_router
from app.api.routes.availability import router as availability_router
from app.api.routes.texting import router as texting_router
from app.api.routes.llm import router as llm_router
from app.api.routes.contacts import router as contacts_router
from app.api.routes.testing import router as testing_router
from app.api.routes.legal import router as legal_router
from app.services.texting_service import TextingService
from app.dependencies import (
    initialize_services,
    get_texting_service_dependency
)


app = FastAPI(
    title="CoffyChat",
    description="Smart Event Scheduling API",
    version="0.1.0"
)

# Mount static files
# Get the absolute path to the static directory
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Create static directory if it doesn't exist
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize all services at startup
initialize_services()

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(events_router, prefix="/events", tags=["events"])
app.include_router(availability_router, prefix="/availability", tags=["availability"])
app.include_router(participants_router, prefix="/participants", tags=["participants"])
app.include_router(texting_router, prefix="/text", tags=["texting"])
app.include_router(llm_router, prefix="/llm", tags=["llm"])
app.include_router(contacts_router, prefix="/contacts", tags=["contacts"])
app.include_router(testing_router, prefix="/testing", tags=["testing"])
app.include_router(legal_router, tags=["legal"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Coffy"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}