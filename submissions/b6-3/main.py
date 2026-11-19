import urllib.parse
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from auth.dependencies import get_optional_user
from config import BASE_DIR
from database import Base, SessionLocal, engine
from exceptions import AppException, AuthRequiredException
from models import Project, Todo, User  # noqa: F401 - Base.metadata 등록
from routers import auth, home, projects, templates, todos, users
from seed import seed_initial_data


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Team Todo Hub (B6-3)",
    description="JWT 인증 · Google OAuth2 · SQLAlchemy 연관관계 기반 팀 할 일 관리 웹 서비스",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(home.router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(todos.router)
app.include_router(users.router)


def _resolve_user_for_error(request: Request) -> User | None:
    db = SessionLocal()
    try:
        return get_optional_user(request=request, db=db)
    finally:
        db.close()


@app.exception_handler(AuthRequiredException)
async def auth_required_handler(_request: Request, exc: AuthRequiredException) -> RedirectResponse:
    """비로그인 사용자가 보호 경로 접근 시 로그인 페이지로 안내 리다이렉트."""
    query = urllib.parse.urlencode(
        {"next": exc.next_url, "message": exc.detail}
    )
    return RedirectResponse(url=f"/login?{query}", status_code=303)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> HTMLResponse:
    """403 Forbidden, 404 Not Found, 400 Bad Request 등 커스텀 예외 공통 처리."""
    current_user = _resolve_user_for_error(request)
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "current_user": current_user,
            "status_code": exc.status_code,
            "title": exc.title,
            "detail": exc.detail,
        },
        status_code=exc.status_code,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> HTMLResponse:
    """존재하지 않는 URL(404) 등 기본 HTTP 예외도 일관된 화면으로 처리."""
    current_user = _resolve_user_for_error(request)
    title = "페이지를 찾을 수 없습니다" if exc.status_code == 404 else "요청을 처리할 수 없습니다"
    detail = (
        "입력하신 주소가 올바른지 확인하거나 아래 버튼을 통해 이동해 주세요."
        if exc.status_code == 404
        else str(exc.detail)
    )
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "current_user": current_user,
            "status_code": exc.status_code,
            "title": title,
            "detail": detail,
        },
        status_code=exc.status_code,
    )
