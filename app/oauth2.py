from jose import JWTError, jwt
from datetime import datetime, timedelta
from config import settings
import schemas, models
import database
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')


SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, [ALGORITHM])
        id: str = payload.get('user_id')
        creator: bool = payload.get('creator')
        username: str = payload.get('username')
        if id is None:
            raise credentials_exception
        token_data = {'user_id': id, 'creator': creator, 'username': username}
    except JWTError:
        raise credentials_exception
    return token_data

async def get_current_user(request: Request):
    try:
        token = request.cookies.get("access_token")
        if token is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])    
        user_id: int = payload.get("user_id")
        creator: bool = payload.get('creator')
        username: str = payload.get('username') 
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid authentication credentials")
        return {"id": user_id, 'creator': creator, 'username': username}
    except JWTError:
        return None
