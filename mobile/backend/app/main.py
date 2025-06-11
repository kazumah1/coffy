from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from fastapi.responses import HTMLResponse

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
    title="Coffy",
    description="Smart Event Scheduling API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://localhost:19006",  # Expo development server
        "exp://localhost:19000",  # Expo Go
        "exp://192.168.1.*:19000",  # Expo Go on local network
        "https://*.coffy.app",  # Production domain (replace with your actual domain)
        "https://coffy.app",  # Production domain (replace with your actual domain)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
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
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
        <head>
            <title>Coffy</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    margin: 0;
                    background-color: #FFFEF7;
                    color: #4A3728;
                }
                .container {
                    text-align: center;
                    padding: 2rem;
                    max-width: 800px;
                    margin: 0 auto;
                }
                h1 {
                    font-size: 2.5rem;
                    margin-bottom: 2rem;
                    color: #8B4513;
                }
                .description {
                    margin: 2rem 0;
                    text-align: left;
                    line-height: 1.6;
                }
                .description p {
                    margin-bottom: 1rem;
                    color: #4A3728;
                }
                .description ul {
                    list-style-type: none;
                    padding: 0;
                    margin: 1.5rem 0;
                }
                .description li {
                    margin: 0.75rem 0;
                    padding-left: 1.5rem;
                    position: relative;
                    color: #6B4E3D;
                }
                .description li:before {
                    content: "•";
                    color: #8B4513;
                    position: absolute;
                    left: 0;
                }
                .links {
                    display: flex;
                    gap: 2rem;
                    justify-content: center;
                    margin-top: 2rem;
                }
                a {
                    color: #8B4513;
                    text-decoration: none;
                    padding: 0.75rem 1.5rem;
                    border: 2px solid #8B4513;
                    border-radius: 8px;
                    transition: all 0.2s ease;
                }
                a:hover {
                    background-color: #8B4513;
                    color: #FFFEF7;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to Coffy</h1>
                <div class="description">
                    <p>Coffy is your AI-powered event scheduling assistant that makes planning gatherings effortless. Whether you're organizing coffee meetups, dinner parties, or team meetings, Coffy helps you:</p>
                    <ul>
                        <li>Find the perfect time that works for everyone</li>
                        <li>Send automated invites and reminders</li>
                        <li>Handle RSVPs and updates in real-time</li>
                        <li>Manage your events through natural conversation</li>
                    </ul>
                    <p>Start planning your next event with Coffy today!</p>
                </div>
                <div class="links">
                    <a href="/privacy-policy">Privacy Policy</a>
                    <a href="/terms">Terms of Service</a>
                </div>
            </div>
        </body>
    </html>
    """)

@app.get("/health")
def health_check():
    return {"status": "healthy"}