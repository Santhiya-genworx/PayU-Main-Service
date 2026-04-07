"""This module provides functions for creating and verifying JSON Web Tokens (JWTs) for access and refresh tokens. It includes functions to create access and refresh tokens with specific expiration times and unique identifiers, as well as functions to verify the validity of these tokens and extract their payloads. The module uses the `jose` library for encoding and decoding JWTs, and it relies on configuration settings for secret keys,"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from src.config.settings import settings


def create_access_token(data: dict[str, Any]) -> tuple[str, str, datetime] | None:
    """Create an access token for the given data.
    Args:
        data: A dictionary containing the data to be encoded in the token.
    Returns:
        A tuple containing the access token, its unique identifier, and expiration time, or None if token creation fails.
    """

    try:
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
        jti = str(uuid.uuid4())

        to_encode.update({"exp": expire, "type": "access", "jti": jti})
        token = jwt.encode(to_encode, settings.access_secret_key, algorithm=settings.algorithm)
        return token, jti, expire
    except JWTError:
        return None


def create_refresh_token(data: dict[str, Any]) -> tuple[str, str, datetime] | None:
    """Create a refresh token for the given data.
    Args:
        data: A dictionary containing the data to be encoded in the token.
    Returns:
        A tuple containing the refresh token, its unique identifier, and expiration time, or None if token creation fails.
    """

    try:
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
        jti = str(uuid.uuid4())

        to_encode.update({"exp": expire, "type": "refresh", "jti": jti})
        token = jwt.encode(to_encode, settings.refresh_secret_key, algorithm=settings.algorithm)
        return token, jti, expire
    except JWTError:
        return None


def verify_access_token(token: str) -> dict[str, Any] | None:
    """Verify an access token and return its payload.
    Args:
        token: The access token to verify.
    Returns:
        The decoded payload if the token is valid and of the correct type, otherwise None.
    """

    try:
        payload = jwt.decode(token, settings.access_secret_key, algorithms=[settings.algorithm])

        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> dict[str, Any] | None:
    """Verify a refresh token and return its payload.
    Args:
        token: The refresh token to verify.
    Returns:
        The decoded payload if the token is valid and of the correct type, otherwise None.
    """

    try:
        payload = jwt.decode(token, settings.refresh_secret_key, algorithms=[settings.algorithm])

        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None
