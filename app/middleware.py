from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth import decode_JWT
from app.models import User
from app.database import SessionLocal

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.cookies.get("access_token")
        
        #по умолчанию current_user = None (guest)
        request.state.current_user = None
        
        if token:
            payload = decode_JWT(token)
            if payload:
                username = payload.get("sub")
                db = SessionLocal()
                try:
                    user = db.query(User).filter(User.username == username).first()
                    if user:
                        request.state.current_user = user
                finally:
                    db.close()
        

        response = await call_next(request)
        return response