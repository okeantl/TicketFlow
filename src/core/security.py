from datetime import datetime, timedelta

import bcrypt
import jwt

from src.core.config import get_settings


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    return hashed.decode()


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def create_access_token(user_id: int) -> str:
    payload = dict(sub=str(user_id), exp=datetime.utcnow() + timedelta(hours=24))
    result = jwt.encode(payload, get_settings().SECRET_KEY, algorithm="HS256")
    return result


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, get_settings().SECRET_KEY, algorithms=["HS256"])
