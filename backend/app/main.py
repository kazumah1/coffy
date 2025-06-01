from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from api.routes import auth
from api.routes.events import router as events_router
from api.routes.participants import router as participants_router
from api.routes.availability import router as availability_router
from api.routes.texting import router as texting_router
from api.routes.llm import router as llm_router
from services.texting_service import TextingService
from dependencies import (
    initialize_services,
    get_texting_service_dependency
)

app = FastAPI(
    title="CoffyChat",
    description="Smart Event Scheduling API",
    version="0.1.0"
)

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

@app.get("/")
def read_root():
    return {"message": "Welcome to W2M app"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}