from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user, get_optional_user
from auth.google_oauth import (
    build_google_authorize_url,
    exchange_code_for_token,
    fetch_google_userinfo,
    generate_oauth_state,
)
from auth.security import create_access_token
from config import (
    ACCESS_TOKEN_COOKIE_NAME,
    COOKIE_SECURE,
    JWT_EXPIRE_MINUTES,
    OAUTH_STATE_COOKIE_NAME,
    is_google_oauth_configured,
)
from database import get_db
from models.user import User
from routers import extract_error_message, safe_next_url, templates
from schemas.auth import SignupForm
from services.auth_service import AuthService

router = APIRouter(tags=["auth"])
auth_service = AuthService()


def _set_auth_cookie(response: RedirectResponse, user: User) -> RedirectResponse:
    token = create_access_token(user_id=user.id, username=user.username)
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=JWT_EXPIRE_MINUTES * 60,
    )
    return response


@router.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    next: str | None = Query(default=None),
    message: str | None = Query(default=None),
    current_user: User | None = Depends(get_optional_user),
):
    if current_user is not None:
        return RedirectResponse(url=safe_next_url(next), status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={
            "current_user": None,
            "next_url": safe_next_url(next),
            "error": None,
            "info_message": message,
            "identifier": "",
            "google_enabled": is_google_oauth_configured(),
        },
    )


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    identifier: str = Form(default=""),
    password: str = Form(default=""),
    next_url: str = Form(default="/projects"),
    db: Session = Depends(get_db),
):
    target_url = safe_next_url(next_url)
    user = auth_service.authenticate(db, identifier=identifier, password=password)
    if user is None:
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={
                "current_user": None,
                "next_url": target_url,
                "error": "아이디(또는 이메일)와 비밀번호를 다시 확인해 주세요.",
                "info_message": None,
                "identifier": identifier,
                "google_enabled": is_google_oauth_configured(),
            },
            status_code=401,
        )

    response = RedirectResponse(url=target_url, status_code=303)
    return _set_auth_cookie(response, user)


@router.get("/signup", response_class=HTMLResponse)
def signup_page(
    request: Request,
    current_user: User | None = Depends(get_optional_user),
):
    if current_user is not None:
        return RedirectResponse(url="/projects", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="auth/signup.html",
        context={
            "current_user": None,
            "error": None,
            "form_data": {"username": "", "email": ""},
            "google_enabled": is_google_oauth_configured(),
        },
    )


@router.post("/signup", response_class=HTMLResponse)
def signup_submit(
    request: Request,
    username: str = Form(default=""),
    email: str = Form(default=""),
    password: str = Form(default=""),
    password_confirm: str = Form(default=""),
    db: Session = Depends(get_db),
):
    try:
        form = SignupForm(
            username=username,
            email=email,
            password=password,
            password_confirm=password_confirm,
        )
        new_user = auth_service.signup(db, form)
    except (ValidationError, ValueError) as exc:
        return templates.TemplateResponse(
            request=request,
            name="auth/signup.html",
            context={
                "current_user": None,
                "error": extract_error_message(exc),
                "form_data": {"username": username, "email": email},
                "google_enabled": is_google_oauth_configured(),
            },
            status_code=400,
        )

    response = RedirectResponse(url="/projects", status_code=303)
    return _set_auth_cookie(response, new_user)


@router.post("/logout")
def logout_submit(current_user: User = Depends(get_current_user)):
    _ = current_user
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE_NAME)
    return response


@router.get("/auth/google/login")
def google_login(request: Request):
    if not is_google_oauth_configured():
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={
                "current_user": None,
                "next_url": "/projects",
                "error": (
                    "Google OAuth2 환경변수(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)가 "
                    "설정되지 않았습니다. README.md의 Google OAuth2 설정 가이드를 참고해 .env에 입력해 주세요."
                ),
                "info_message": None,
                "identifier": "",
                "google_enabled": False,
            },
            status_code=503,
        )

    state = generate_oauth_state()
    authorize_url = build_google_authorize_url(state)
    response = RedirectResponse(url=authorize_url, status_code=302)
    response.set_cookie(
        key=OAUTH_STATE_COOKIE_NAME,
        value=state,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=300,
    )
    return response


@router.get("/auth/google/callback")
def google_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    saved_state = request.cookies.get(OAUTH_STATE_COOKIE_NAME)

    if error or not code or not state or state != saved_state:
        response = templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={
                "current_user": None,
                "next_url": "/projects",
                "error": "Google 로그인 인증이 취소되었거나 상태 검증(state)에 실패했습니다.",
                "info_message": None,
                "identifier": "",
                "google_enabled": is_google_oauth_configured(),
            },
            status_code=400,
        )
        response.delete_cookie(key=OAUTH_STATE_COOKIE_NAME)
        return response

    try:
        token_data = exchange_code_for_token(code)
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("Google 액세스 토큰을 받지 못했습니다.")

        userinfo = fetch_google_userinfo(access_token)
        google_id = str(userinfo.get("id", ""))
        email = str(userinfo.get("email", ""))
        name = userinfo.get("name")
        if not google_id or not email:
            raise ValueError("Google 계정 이메일 정보를 확인할 수 없습니다.")

        user = auth_service.get_or_create_google_user(
            db,
            google_id=google_id,
            email=email,
            name=name,
        )
    except ValueError as exc:
        response = templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={
                "current_user": None,
                "next_url": "/projects",
                "error": str(exc),
                "info_message": None,
                "identifier": "",
                "google_enabled": is_google_oauth_configured(),
            },
            status_code=400,
        )
        response.delete_cookie(key=OAUTH_STATE_COOKIE_NAME)
        return response

    response = RedirectResponse(url="/projects", status_code=303)
    response.delete_cookie(key=OAUTH_STATE_COOKIE_NAME)
    return _set_auth_cookie(response, user)
