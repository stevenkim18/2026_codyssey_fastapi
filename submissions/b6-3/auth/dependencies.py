from fastapi import Depends, Request
from sqlalchemy.orm import Session

from auth.security import decode_access_token
from config import ACCESS_TOKEN_COOKIE_NAME
from database import get_db
from exceptions import AuthRequiredException
from models.user import User
from repositories.user_repository import UserRepository

user_repository = UserRepository()


def _extract_token(request: Request) -> str | None:
    """HttpOnly 쿠키 또는 Authorization Bearer 헤더에서 JWT를 추출합니다."""
    cookie_token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    return None


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    """공개 경로용 Depends: 로그인 상태면 User를, 아니면 None을 반환합니다."""
    token = _extract_token(request)
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        return None

    return user_repository.find_by_id(db, user_id)


def get_current_user(
    request: Request,
    user: User | None = Depends(get_optional_user),
) -> User:
    """보호 경로용 Depends: 비로그인 요청을 차단하고 AuthRequiredException을 발생시킵니다."""
    if user is None:
        next_url = request.url.path
        if request.url.query:
            next_url = f"{next_url}?{request.url.query}"
        raise AuthRequiredException(next_url=next_url)
    return user
