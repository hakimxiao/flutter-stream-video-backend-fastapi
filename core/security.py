from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session
import jwt

from core.config import settings
from database.connection import get_db
from models.user import User


bearer_schema = HTTPBearer(auto_error=False)


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )


def get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_schema),
        db: Session = Depends(get_db)
) -> User:
    # 1. Check token tersedia
    if credentials is None:
        raise unauthorized()

    # 2. Verify JWT dan ambil payload
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp"]}
        )

        # 3. Validasi identitas di dalam token
        subject = payload.get("sub")

        if not isinstance(subject, str) or not subject.isdecimal():
            raise ValueError("Invalid subject")

        user_id = int(subject)

    except (InvalidTokenError, TypeError, ValueError):
        raise unauthorized()

    # 4. Cek id pengguna beneran ada di db
    user = db.get(User, user_id)

    if user is None:
        raise unauthorized()

    # 5. Kembalikan object user
    return user