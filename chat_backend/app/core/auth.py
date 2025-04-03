from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Optional
import jwt
from pydantic import ValidationError
import asyncio

from ..models.models import TokenData, User, UserInDB
from ..db.database import get_user_by_username

# JWT Configuration
SECRET_KEY = "your-secret-key-for-jwt"  # In production, use a secure key and store it in environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password: str) -> str:
    # For a real app, use passlib or another robust hashing library
    return f"hashed_{password}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashed_password == f"hashed_{plain_password}"

async def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = await get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except (jwt.PyJWTError, ValidationError):
        raise credentials_exception

    user_in_db = await get_user_by_username(token_data.username)
    if user_in_db is None:
        raise credentials_exception

    return User(
        id=user_in_db.id,
        username=user_in_db.username,
        email=user_in_db.email,
        role=user_in_db.role,
        created_at=user_in_db.created_at
    )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user

# Role-based access control
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    print(f"Checking admin access for user: {current_user.username}, role: {current_user.role}")
    if current_user.role != "admin":
        print(f"Access denied: User {current_user.username} has role {current_user.role} instead of 'admin'")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    print(f"Admin access granted for user: {current_user.username}")
    return current_user