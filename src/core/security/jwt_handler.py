from datetime import datetime, timedelta
import uuid
from src.core.config.settings import settings
from jose import JWTError, jwt

def create_access_token(data: dict):
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes = settings.access_token_expire_minutes)
        jti = str(uuid.uuid4())

        to_encode.update({
            "exp": expire,
            "type": "access",
            "jti": jti
        })
        token = jwt.encode(to_encode, settings.access_secret_key, algorithm = settings.algorithm)
        return token, jti, expire
    except JWTError:
        return None

def create_refresh_token(data: dict):
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days = settings.refresh_token_expire_days)
        jti = str(uuid.uuid4())

        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "jti": jti
        })
        token = jwt.encode(to_encode, settings.refresh_secret_key, algorithm = settings.algorithm)
        return token, jti, expire
    except JWTError:
        return None

def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.access_secret_key, algorithms = [settings.algorithm])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None
    
def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, settings.refresh_secret_key, algorithms = [settings.algorithm])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None