from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from auth.dependencies import get_optional_user
from database import get_db
from models.project import Project
from models.todo import Todo
from models.user import User
from routers import templates

router = APIRouter(tags=["home"])


@router.get("/", response_class=HTMLResponse)
def read_home(
    request: Request,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    stats = {
        "users": db.query(User).count(),
        "projects": db.query(Project).count(),
        "todos": db.query(Todo).count(),
        "done_todos": db.query(Todo).filter(Todo.status == "done").count(),
    }
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "current_user": current_user,
            "stats": stats,
        },
    )
