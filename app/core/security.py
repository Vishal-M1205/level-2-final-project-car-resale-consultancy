from typing import Optional
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash
from app.core.config import config
from app.core.scopes import ROLE_SCOPES
import jwt

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_hashed_password(hashed_password: str, password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(token_payload: dict, expiration_minutes: Optional[int] = None):
    encode_data = token_payload.copy()

    if expiration_minutes:
        encode_data.update(
            {"exp": datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)}
        )
    else:
        encode_data.update(
            {
                "exp": datetime.now(timezone.utc)
                + timedelta(minutes=config.jwt_access_expiration_minute)
            }
        )

    scopes = ROLE_SCOPES[encode_data.get("role", "CUSTOMER")]

    encode_data.update({"scopes": scopes, "type": "access"})

    return jwt.encode(
        payload=encode_data, key=config.jwt_secret_key, algorithm=config.jwt_algorithm
    )


def create_refresh_token(token_payload):
    encode_data = token_payload.copy()
    expiration_day = datetime.now(timezone.utc) + timedelta(
        days=config.jwt_refresh_expiration_days
    )
    encode_data.update({"exp": expiration_day, "type": "refresh"})

    return jwt.encode(
        payload=encode_data, key=config.jwt_secret_key, algorithm=config.jwt_algorithm
    )


def decode_token(token: str):
    return jwt.decode(
        jwt=token, key=config.jwt_secret_key, algorithms=[config.jwt_algorithm]
    )
