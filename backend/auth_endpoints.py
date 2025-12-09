# Authentication endpoints for api.py
# Add these to your backend/api.py file

from backend.auth import UserManager
from fastapi import Header

# Initialize user manager (add this with other global variables)
user_manager = UserManager()

@app.post("/auth/register")
async def register(request: Dict[str, Any]):
    """Register a new user"""
    user_id = request.get("user_id")
    password = request.get("password")
    
    if not user_id or not password:
        raise HTTPException(status_code=400, detail="user_id and password required")
    
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    result = user_manager.register_user(user_id, password)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@app.post("/auth/login")
async def login(request: Dict[str, Any]):
    """Login and get session token"""
    user_id = request.get("user_id")
    password = request.get("password")
    
    if not user_id or not password:
        raise HTTPException(status_code=400, detail="user_id and password required")
    
    session_token = user_manager.authenticate(user_id, password)
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "status": "success",
        "session_token": session_token,
        "user_id": user_id
    }


@app.post("/auth/logout")
async def logout(request: Dict[str, Any]):
    """Logout user"""
    session_token = request.get("session_token")
    
    if session_token:
        user_manager.logout(session_token)
    
    return {"status": "success", "message": "Logged out"}


@app.get("/auth/verify")
async def verify_session(authorization: Optional[str] = Header(None)):
    """Verify session token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    # Extract token from "Bearer <token>"
    token = authorization.replace("Bearer ", "")
    user_id = user_manager.verify_session(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return {
        "status": "success",
        "user_id": user_id
    }


@app.get("/auth/check-user/{user_id}")
async def check_user_exists(user_id: str):
    """Check if user exists"""
    exists = user_manager.user_exists(user_id)
    return {
        "exists": exists,
        "user_id": user_id
    }


@app.post("/auth/change-password")
async def change_password(request: Dict[str, Any], authorization: Optional[str] = Header(None)):
    """Change user password"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    user_id = user_manager.verify_session(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    old_password = request.get("old_password")
    new_password = request.get("new_password")
    
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="old_password and new_password required")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    result = user_manager.change_password(user_id, old_password, new_password)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result
