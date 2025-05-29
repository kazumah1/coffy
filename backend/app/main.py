from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import auth

app = FastAPI(
    title="W2M But Better",
    description="Smart Event Scheduling API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
def read_root():
    return {"message": "Welcome to W2M app"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}