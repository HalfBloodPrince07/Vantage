# User Authentication System
# backend/auth.py

from typing import Optional, Dict
import hashlib
import secrets
from datetime import datetime, timedelta
import json
from pathlib import Path

class UserManager:
    """Simple file-based user management with password hashing"""
    
    def __init__(self, users_file: str = "locallens_users.json"):
        self.users_file = Path(users_file)
        self.users = self._load_users()
        self.sessions = {}  # session_token -> user_id
    
    def _load_users(self) -> Dict:
        """Load users from file"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_users(self):
        """Save users to file"""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, user_id: str, password: str) -> Dict:
        """Register a new user"""
        if user_id in self.users:
            return {"status": "error", "message": "User already exists"}
        
        self.users[user_id] = {
            "password_hash": self._hash_password(password),
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        self._save_users()
        
        return {"status": "success", "message": "User registered successfully"}
    
    def authenticate(self, user_id: str, password: str) -> Optional[str]:
        """
        Authenticate user and return session token
        Returns None if authentication fails
        """
        if user_id not in self.users:
            return None
        
        password_hash = self._hash_password(password)
        if self.users[user_id]["password_hash"] != password_hash:
            return None
        
        # Update last login
        self.users[user_id]["last_login"] = datetime.now().isoformat()
        self._save_users()
        
        # Create session token
        session_token = secrets.token_urlsafe(32)
        self.sessions[session_token] = {
            "user_id": user_id,
            "created_at": datetime.now()
        }
        
        return session_token
    
    def verify_session(self, session_token: str) -> Optional[str]:
        """Verify session token and return user_id"""
        if session_token not in self.sessions:
            return None
        
        session = self.sessions[session_token]
        
        # Check if session expired (24 hours)
        if datetime.now() - session["created_at"] > timedelta(hours=24):
            del self.sessions[session_token]
            return None
        
        return session["user_id"]
    
    def logout(self, session_token: str):
        """Logout user by removing session"""
        if session_token in self.sessions:
            del self.sessions[session_token]
    
    def user_exists(self, user_id: str) -> bool:
        """Check if user exists"""
        return user_id in self.users
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> Dict:
        """Change user password"""
        if user_id not in self.users:
            return {"status": "error", "message": "User not found"}
        
        # Verify old password
        if self._hash_password(old_password) != self.users[user_id]["password_hash"]:
            return {"status": "error", "message": "Incorrect password"}
        
        # Update password
        self.users[user_id]["password_hash"] = self._hash_password(new_password)
        self._save_users()
        
        return {"status": "success", "message": "Password changed successfully"}
