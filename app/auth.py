import os
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

SECRET_KEY= os.getenv("SECRET_KEY")
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES= 30

pwd_context= CryptContext(schemes=["bcrypt"], deprecated= "auto")

def hash_password(plain: str) -> str:
    """Hash a plain-text password.

    Args:
        plain: The plain-text password to hash.

    Returns:
        The hashed password string.
    """
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed:str) -> bool:
    """Verify a password against its stored hash.

    Args:
        plain: The plain-text password to verify.
        hashed: The stored hashed password.

    Returns:
        True if the password matches the hash, otherwise False.
    """
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    """Create a JWT access token for a user.

    Args:
        user_id: The ID of the user who will own the token.

    Returns:
        A signed JWT containing the user ID and expiration time.
    """
    expire= datetime.now(timezone.utc) + timedelta(minutes= ACCESS_TOKEN_EXPIRE_MINUTES)
    payload= {
        "sub": str(user_id),
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> int | None:
    """Decode a JWT access token and retrieve its user ID.

    Args:
        token: The JWT access token to decode and validate.

    Returns:
        The user ID if the token is valid and contains a valid user ID;
        otherwise, None.
    """
    try:
        payload= jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None