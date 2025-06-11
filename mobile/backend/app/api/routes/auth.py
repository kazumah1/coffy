from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from app.services.google_oauth_service import GoogleOAuthHandler
from app.services.token_manager import TokenManager
from app.services.database_service import DatabaseService
from app.dependencies import get_oauth_handler, get_token_manager, get_database_service
from app.models.update_profile_request import UpdateProfileRequest
from jose import jwt


router = APIRouter()

@router.get("/google/login")
async def google_login(oauth_handler: GoogleOAuthHandler = Depends(get_oauth_handler)):
    auth_url, _ = oauth_handler.get_authorization_url()
    return RedirectResponse(url=auth_url)

@router.get("/google/callback")
async def google_callback(
    code: str,
    oauth_handler: GoogleOAuthHandler = Depends(get_oauth_handler),
    token_manager: TokenManager = Depends(get_token_manager),
    db_service: DatabaseService = Depends(get_database_service)
):
    try:
        # Get credentials
        credentials = oauth_handler.handle_callback(code)
        
        # Extract user info from ID token
        id_token = credentials.id_token
        payload = jwt.get_unverified_claims(id_token)
        email = payload.get('email')
        name = payload.get('name')
        if not email:
            raise HTTPException(status_code=400, detail="Email not found in Google ID token")
        
        # Get or create user by email
        user = await db_service.get_user_by_email(email)
        if not user:
            user = await db_service.create_user(name=name, email=email)
        
        # Store tokens
        await token_manager.store_token(
            user_id=user['id'],
            access_token=credentials.token,
            refresh_token=credentials.refresh_token
        )
        
        # Return success page with user info
        return HTMLResponse(content=f"""
            <html>
                <body>
                    <h2>Login Successful!</h2>
                    <p>You can close this window and return to the app.</p>
                    <p>If you are not redirected automatically, <a href='coffy://auth?email={email}&user_id={user['id']}&name={name}'>tap here to return to the app</a>.</p>
                    <script>
                        window.location.href = "coffy://auth?email={email}&user_id={user['id']}&name={name}"
                    </script>
                </body>
            </html>
        """)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}")
async def get_user(user_id: str, db_service: DatabaseService = Depends(get_database_service)):
    user = await db_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/user/google/{google_id}")
async def get_user_by_google_id(google_id: str, db_service: DatabaseService = Depends(get_database_service)):
    user = await db_service.get_user_by_google_id(google_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/google/refresh")
async def google_refresh(user_id: str, token_manager: TokenManager = Depends(get_token_manager)):
    try:
        await token_manager.refresh_token(user_id)
        return {"message": "Token refreshed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/google/revoke")
async def google_revoke(user_id: str, token_manager: TokenManager = Depends(get_token_manager)):
    return {"message": "No revoke logic implemented"}

@router.post("/users/update-profile")
async def update_profile(request: UpdateProfileRequest, db_service: DatabaseService = Depends(get_database_service)):
    print("Updating profile", request.user_id, request.name, request.email, request.phone_number)
    user = await db_service.update_user(request.user_id, request.name, request.email, request.phone_number, request.contacts_loaded)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user