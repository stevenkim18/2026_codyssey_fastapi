from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from database import BASE_DIR, Base, engine
from models.todo import Todo  # noqa: F401 - Base.metadata에 테이블 등록을 위해 임포트
from routers import home, todos


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="할 일 관리 웹 서비스 (B6-2)",
    description="FastAPI + SQLAlchemy + Jinja2 기반 할 일 CRUD 웹 애플리케이션",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(home.router)
app.include_router(todos.router)
