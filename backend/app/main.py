from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import auth
from api.routes.events import router as events_router
from api.routes.participants import router as participants_router
from api.routes.availability import router as availability_router
from api.routes.texting import router as texting_router

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

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(events_router, prefix="/events", tags=["events"])
app.include_router(availability_router, prefix="/availability", tags=["availability"])
app.include_router(participants_router, prefix="/participants", tags=["participants"])
app.include_router(texting_router, prefix="/texting", tags=["texting"])

@app.get("/")
def read_root():
    return {"message": "Welcome to W2M app"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}