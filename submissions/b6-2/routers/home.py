from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from database import get_db
from routers import templates
from services.todo_service import TodoService

router = APIRouter(tags=["home"])
todo_service = TodoService()


@router.get("/", response_class=HTMLResponse)
def read_home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    summary = todo_service.get_summary(db)
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"summary": summary},
    )
