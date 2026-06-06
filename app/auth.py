from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User
from app.database import get_db

pwd_context = CryptContext(
        schemes=["bcrypt"],
        default="bcrypt",
        deprecated="auto"
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def hash_password(passwordString: str) -> str:
    return pwd_context.hash(passwordString)

def check_password(passwordPlain: str, passwordHash: str) -> bool:
    return pwd_context.verify(passwordPlain, passwordHash)

def create_JWT(username: str, role: str) -> str:
    to_encode = {"sub":username, "role":role}
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, settings.ALGORITHM)

def decode_JWT(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, settings.ALGORITHM)
        return payload
    except JWTError:
        return None

def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    payload = decode_JWT(token)
    if payload:
        username = payload["sub"]
        user = db.query(User).filter(User.username == username).first()
        if user:
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Пользователь не найден",
                headers={"WWW-Authenticate": "Bearer"},
                )
    else:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Неверный токен",
                headers={"WWW-Authenticate": "Bearer"},
                )
    
def require_role(allowed_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав"
            )
        return current_user
    return role_checker
    


