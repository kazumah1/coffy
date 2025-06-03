from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import random
import time
import asyncio

app = FastAPI(title="Coffy Backend API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
user_availability = {}
coffee_spots = [
    {
        "id": "1",
        "name": "Moonrise Coffee",
        "rating": 4.8,
        "distance": "0.3 mi",
        "vibe": "Cozy & Quiet",
        "weatherScore": 95,
        "latitude": 37.7749,
        "longitude": -122.4194
    },
    {
        "id": "2", 
        "name": "Ritual Coffee",
        "rating": 4.6,
        "distance": "0.5 mi",
        "vibe": "Vibrant & Social",
        "weatherScore": 88,
        "latitude": 37.7849,
        "longitude": -122.4094
    },
    {
        "id": "3",
        "name": "Blue Bottle",
        "rating": 4.7,
        "distance": "0.7 mi", 
        "vibe": "Modern & Clean",
        "weatherScore": 92,
        "latitude": 37.7649,
        "longitude": -122.4294
    }
]

# Data Models
class AvailabilityStatus(BaseModel):
    status: str  # 'available', 'maybe', 'busy'
    message: Optional[str] = None
    location: Optional[dict] = None

class Friend(BaseModel):
    id: str
    name: str
    status: str
    distance: float
    lastSeen: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class CoffeeSpot(BaseModel):
    id: str
    name: str
    rating: float
    distance: str
    vibe: str
    weatherScore: int
    latitude: float
    longitude: float

class CoordinationRequest(BaseModel):
    user_id: str
    friend_ids: List[str]
    spot_id: str
    message: Optional[str] = None

# Coffee Radar Endpoints

@app.post("/api/radar/set-availability")
async def set_user_availability(user_id: str, availability: AvailabilityStatus):
    """Set user's current availability status"""
    user_availability[user_id] = {
        "status": availability.status,
        "message": availability.message,
        "location": availability.location,
        "updated_at": time.time()
    }
    return {"success": True, "message": "Availability updated"}

@app.get("/api/radar/friends-availability/{user_id}")
async def get_friends_availability(user_id: str):
    """Get real-time availability of user's coffee crew"""
    
    # Simulate getting user's coffee crew (in production, from database)
    # For demo, we'll generate some mock friends with real-time status
    mock_friends = [
        {"id": "1", "name": "Sarah Chen", "base_status": "available"},
        {"id": "2", "name": "Mike Johnson", "base_status": "maybe"}, 
        {"id": "3", "name": "Emma Davis", "base_status": "busy"},
        {"id": "4", "name": "Alex Rodriguez", "base_status": "available"},
        {"id": "5", "name": "Jessica Wang", "base_status": "maybe"},
    ]
    
    friends_with_status = []
    for friend in mock_friends:
        # Add some randomness to simulate real-time changes
        statuses = ["available", "maybe", "busy"]
        current_status = random.choice(statuses) if random.random() > 0.7 else friend["base_status"]
        
        friends_with_status.append({
            "id": friend["id"],
            "name": friend["name"],
            "status": current_status,
            "distance": round(random.uniform(0.1, 10.0), 1),
            "lastSeen": random.choice(["Just now", "2m ago", "5m ago", "15m ago", "1h ago"]),
            "latitude": 37.7749 + random.uniform(-0.01, 0.01),
            "longitude": -122.4194 + random.uniform(-0.01, 0.01)
        })
    
    return {
        "success": True,
        "friends": friends_with_status,
        "updated_at": time.time()
    }

@app.get("/api/radar/coffee-spots")
async def get_coffee_spot_recommendations(
    user_lat: float = 37.7749,
    user_lng: float = -122.4194,
    group_size: int = 2,
    weather_preference: str = "any"
):
    """Get personalized coffee spot recommendations"""
    
    # Simulate weather-aware and group-size-aware recommendations
    recommendations = []
    for spot in coffee_spots:
        # Calculate mock distance
        distance_km = abs(spot["latitude"] - user_lat) + abs(spot["longitude"] - user_lng)
        distance_mi = round(distance_km * 69, 1)  # Rough conversion
        
        # Adjust score based on group size and weather
        score = spot["weatherScore"]
        if group_size > 4 and "Social" in spot["vibe"]:
            score += 10
        elif group_size <= 2 and "Quiet" in spot["vibe"]:
            score += 10
            
        spot_with_score = {
            **spot,
            "distance": f"{distance_mi} mi",
            "recommendationScore": min(score, 100),
            "groupSuitability": "Perfect" if score > 90 else "Good" if score > 80 else "Okay"
        }
        recommendations.append(spot_with_score)
    
    # Sort by recommendation score
    recommendations.sort(key=lambda x: x["recommendationScore"], reverse=True)
    
    return {
        "success": True,
        "recommendations": recommendations[:3],  # Top 3
        "weather_optimized": True
    }

@app.post("/api/radar/coordinate")
async def coordinate_instant_coffee(request: CoordinationRequest):
    """Coordinate instant coffee meetup"""
    
    # Get the selected coffee spot
    selected_spot = next((spot for spot in coffee_spots if spot["id"] == request.spot_id), None)
    if not selected_spot:
        raise HTTPException(status_code=404, detail="Coffee spot not found")
    
    # Simulate sending notifications to friends
    notifications_sent = []
    for friend_id in request.friend_ids:
        # In production, this would send real push notifications
        notification = {
            "friend_id": friend_id,
            "type": "coffee_invite",
            "spot": selected_spot,
            "organizer_id": request.user_id,
            "message": request.message or f"☕ Coffee at {selected_spot['name']} right now?",
            "eta_minutes": random.randint(5, 20),
            "sent_at": time.time()
        }
        notifications_sent.append(notification)
    
    # Simulate some friends accepting/declining
    responses = []
    for notification in notifications_sent:
        response_type = random.choice(["accepted", "maybe", "declined"])
        responses.append({
            "friend_id": notification["friend_id"],
            "response": response_type,
            "eta_minutes": notification["eta_minutes"] if response_type == "accepted" else None
        })
    
    return {
        "success": True,
        "coordination_id": f"coord_{int(time.time())}",
        "spot": selected_spot,
        "notifications_sent": len(notifications_sent),
        "responses": responses,
        "estimated_meetup_time": int(time.time()) + 900  # 15 minutes from now
    }

@app.get("/api/radar/active-coordinations/{user_id}")
async def get_active_coordinations(user_id: str):
    """Get user's active coffee coordinations"""
    
    # Mock active coordination
    mock_coordination = {
        "id": "coord_12345",
        "spot": coffee_spots[0],
        "status": "active",
        "participants": [
            {"id": "1", "name": "Sarah Chen", "status": "accepted", "eta": "8 min"},
            {"id": "2", "name": "Mike Johnson", "status": "maybe", "eta": "12 min"}
        ],
        "meetup_time": int(time.time()) + 600,  # 10 minutes
        "created_at": time.time() - 300  # 5 minutes ago
    }
    
    return {
        "success": True,
        "active_coordinations": [mock_coordination] if random.random() > 0.5 else [],
        "total_today": random.randint(0, 3)
    }

# Weather Integration Endpoint
@app.get("/api/radar/weather-context")
async def get_weather_context(lat: float = 37.7749, lng: float = -122.4194):
    """Get weather context for coffee recommendations"""
    
    # Mock weather data (in production, integrate with weather API)
    weather_conditions = ["sunny", "cloudy", "rainy", "foggy"]
    current_weather = random.choice(weather_conditions)
    
    recommendations = {
        "sunny": {"preference": "outdoor", "message": "Perfect weather for patio coffee!"},
        "cloudy": {"preference": "any", "message": "Great day for any coffee spot"},
        "rainy": {"preference": "indoor", "message": "Cozy indoor vibes recommended"},
        "foggy": {"preference": "warm", "message": "Perfect for a warm, inviting spot"}
    }
    
    return {
        "success": True,
        "weather": {
            "condition": current_weather,
            "temperature": random.randint(60, 80),
            "recommendation": recommendations[current_weather]
        },
        "coffee_mood": random.choice(["energizing", "relaxing", "social", "focused"])
    }

@app.get("/")
async def root():
    return {"message": "Coffy Backend API - Coffee Radar Ready! ☕⚡"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 