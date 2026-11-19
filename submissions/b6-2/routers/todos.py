from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from database import get_db
from routers import templates
from schemas.todo import TodoCreate, TodoUpdate
from services.todo_service import TodoService

router = APIRouter(prefix="/todos", tags=["todos"])
todo_service = TodoService()


def _extract_error_message(exc: ValidationError | ValueError) -> str:
    if isinstance(exc, ValidationError):
        first_error = exc.errors()[0]
        msg = str(first_error.get("msg", "입력값을 다시 확인해 주세요."))
        return msg.removeprefix("Value error, ")
    return str(exc)


@router.get("", response_class=HTMLResponse)
def list_todos(
    request: Request,
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    todos = todo_service.get_todos(db, keyword=q)
    summary = todo_service.get_summary(db)
    return templates.TemplateResponse(
        request=request,
        name="todos/list.html",
        context={
            "todos": todos,
            "keyword": (q or "").strip(),
            "summary": summary,
        },
    )


@router.get("/new", response_class=HTMLResponse)
def new_todo_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="todos/create.html",
        context={
            "error": None,
            "form_data": {"title": "", "description": "", "due_date": ""},
        },
    )


@router.post("", response_class=HTMLResponse)
def create_todo(
    request: Request,
    title: str = Form(default=""),
    description: str = Form(default=""),
    due_date: str = Form(default=""),
    db: Session = Depends(get_db),
):
    try:
        parsed_due_date = todo_service.parse_due_date(due_date)
        todo_data = TodoCreate(
            title=title,
            description=description,
            due_date=parsed_due_date,
        )
    except (ValidationError, ValueError) as exc:
        return templates.TemplateResponse(
            request=request,
            name="todos/create.html",
            context={
                "error": _extract_error_message(exc),
                "form_data": {
                    "title": title,
                    "description": description,
                    "due_date": due_date,
                },
            },
            status_code=400,
        )

    todo_service.create_todo(db, todo_data)
    return RedirectResponse(url="/todos", status_code=303)


@router.get("/{todo_id}", response_class=HTMLResponse)
def detail_todo(
    request: Request,
    todo_id: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    todo = todo_service.get_todo(db, todo_id)
    if todo is None:
        return templates.TemplateResponse(
            request=request,
            name="todos/not_found.html",
            context={"todo_id": todo_id},
            status_code=404,
        )

    return templates.TemplateResponse(
        request=request,
        name="todos/detail.html",
        context={"todo": todo},
    )


@router.get("/{todo_id}/edit", response_class=HTMLResponse)
def edit_todo_form(
    request: Request,
    todo_id: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    todo = todo_service.get_todo(db, todo_id)
    if todo is None:
        return templates.TemplateResponse(
            request=request,
            name="todos/not_found.html",
            context={"todo_id": todo_id},
            status_code=404,
        )

    return templates.TemplateResponse(
        request=request,
        name="todos/edit.html",
        context={
            "todo": todo,
            "error": None,
            "form_data": {
                "title": todo.title,
                "description": todo.description or "",
                "due_date": todo.due_date.isoformat() if todo.due_date else "",
                "is_completed": todo.is_completed,
            },
        },
    )


@router.post("/{todo_id}/edit", response_class=HTMLResponse)
def update_todo(
    request: Request,
    todo_id: int,
    title: str = Form(default=""),
    description: str = Form(default=""),
    due_date: str = Form(default=""),
    is_completed: bool = Form(default=False),
    db: Session = Depends(get_db),
):
    existing = todo_service.get_todo(db, todo_id)
    if existing is None:
        return templates.TemplateResponse(
            request=request,
            name="todos/not_found.html",
            context={"todo_id": todo_id},
            status_code=404,
        )

    try:
        parsed_due_date = todo_service.parse_due_date(due_date)
        todo_data = TodoUpdate(
            title=title,
            description=description,
            due_date=parsed_due_date,
            is_completed=is_completed,
        )
    except (ValidationError, ValueError) as exc:
        return templates.TemplateResponse(
            request=request,
            name="todos/edit.html",
            context={
                "todo": existing,
                "error": _extract_error_message(exc),
                "form_data": {
                    "title": title,
                    "description": description,
                    "due_date": due_date,
                    "is_completed": is_completed,
                },
            },
            status_code=400,
        )

    todo_service.update_todo(db, todo_id, todo_data)
    return RedirectResponse(url=f"/todos/{todo_id}", status_code=303)


@router.post("/{todo_id}/toggle")
def toggle_todo(
    request: Request,
    todo_id: int,
    next_url: str = Form(default="/todos"),
    db: Session = Depends(get_db),
):
    updated = todo_service.toggle_todo(db, todo_id)
    if updated is None:
        return templates.TemplateResponse(
            request=request,
            name="todos/not_found.html",
            context={"todo_id": todo_id},
            status_code=404,
        )

    safe_next = next_url if next_url.startswith("/") and not next_url.startswith("//") else "/todos"
    return RedirectResponse(url=safe_next, status_code=303)


@router.post("/{todo_id}/delete")
def delete_todo(
    request: Request,
    todo_id: int,
    db: Session = Depends(get_db),
):
    deleted = todo_service.delete_todo(db, todo_id)
    if not deleted:
        return templates.TemplateResponse(
            request=request,
            name="todos/not_found.html",
            context={"todo_id": todo_id},
            status_code=404,
        )

    return RedirectResponse(url="/todos", status_code=303)
