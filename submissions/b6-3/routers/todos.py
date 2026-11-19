from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database import get_db
from exceptions import ForbiddenException
from models.user import User
from routers import extract_error_message, safe_next_url, templates
from schemas.todo import TodoCreate, TodoUpdate
from services.project_service import ProjectService
from services.todo_service import TodoService

router = APIRouter(prefix="/todos", tags=["todos"])
todo_service = TodoService()
project_service = ProjectService()


@router.get("", response_class=HTMLResponse)
def list_todos(
    request: Request,
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    project_id: str | None = Query(default=None),
    mine: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    parsed_project_id = int(project_id) if project_id and project_id.isdigit() else None
    only_mine = mine == "true"

    todos = todo_service.list_todos(
        db,
        keyword=q,
        status=status,
        project_id=parsed_project_id,
        author_id=current_user.id if only_mine else None,
    )
    projects = project_service.list_projects(db)

    return templates.TemplateResponse(
        request=request,
        name="todos/list.html",
        context={
            "current_user": current_user,
            "todos": todos,
            "projects": projects,
            "keyword": (q or "").strip(),
            "selected_status": status or "",
            "selected_project_id": parsed_project_id,
            "only_mine": only_mine,
        },
    )


@router.get("/new", response_class=HTMLResponse)
def new_todo_form(
    request: Request,
    project_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    projects = project_service.list_projects(db)
    return templates.TemplateResponse(
        request=request,
        name="todos/create.html",
        context={
            "current_user": current_user,
            "projects": projects,
            "error": None,
            "form_data": {
                "title": "",
                "description": "",
                "due_date": "",
                "project_id": project_id or (projects[0].id if projects else ""),
            },
        },
    )


@router.post("", response_class=HTMLResponse)
def create_todo(
    request: Request,
    title: str = Form(default=""),
    description: str = Form(default=""),
    due_date: str = Form(default=""),
    project_id: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    projects = project_service.list_projects(db)
    try:
        if not project_id.isdigit():
            raise ValueError("소속 프로젝트를 선택해 주세요.")
        parsed_due_date = todo_service.parse_due_date(due_date)
        data = TodoCreate(
            title=title,
            description=description,
            due_date=parsed_due_date,
            project_id=int(project_id),
        )
        created = todo_service.create_todo(db, data, current_user)
    except (ValidationError, ValueError) as exc:
        return templates.TemplateResponse(
            request=request,
            name="todos/create.html",
            context={
                "current_user": current_user,
                "projects": projects,
                "error": extract_error_message(exc),
                "form_data": {
                    "title": title,
                    "description": description,
                    "due_date": due_date,
                    "project_id": int(project_id) if project_id.isdigit() else "",
                },
            },
            status_code=400,
        )

    return RedirectResponse(url=f"/todos/{created.id}", status_code=303)


@router.get("/{todo_id}", response_class=HTMLResponse)
def detail_todo(
    request: Request,
    todo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    todo = todo_service.get_todo(db, todo_id)
    can_change_status = (
        todo.author_id == current_user.id or todo.project.owner_id == current_user.id
    )
    return templates.TemplateResponse(
        request=request,
        name="todos/detail.html",
        context={
            "current_user": current_user,
            "todo": todo,
            "can_change_status": can_change_status,
        },
    )


@router.get("/{todo_id}/edit", response_class=HTMLResponse)
def edit_todo_form(
    request: Request,
    todo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    todo = todo_service.get_todo(db, todo_id)
    if todo.author_id != current_user.id:
        raise ForbiddenException("본인이 작성한 할 일만 수정할 수 있습니다.")

    projects = project_service.list_projects(db)
    return templates.TemplateResponse(
        request=request,
        name="todos/edit.html",
        context={
            "current_user": current_user,
            "todo": todo,
            "projects": projects,
            "error": None,
            "form_data": {
                "title": todo.title,
                "description": todo.description or "",
                "due_date": todo.due_date.isoformat() if todo.due_date else "",
                "project_id": todo.project_id,
                "status": todo.status,
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
    project_id: str = Form(default=""),
    status: str = Form(default="todo"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    todo = todo_service.get_todo(db, todo_id)
    if todo.author_id != current_user.id:
        raise ForbiddenException("본인이 작성한 할 일만 수정할 수 있습니다.")

    projects = project_service.list_projects(db)
    try:
        if not project_id.isdigit():
            raise ValueError("소속 프로젝트를 선택해 주세요.")
        parsed_due_date = todo_service.parse_due_date(due_date)
        data = TodoUpdate(
            title=title,
            description=description,
            due_date=parsed_due_date,
            project_id=int(project_id),
            status=status,
        )
        todo_service.update_todo(db, todo_id, data, current_user)
    except (ValidationError, ValueError) as exc:
        return templates.TemplateResponse(
            request=request,
            name="todos/edit.html",
            context={
                "current_user": current_user,
                "todo": todo,
                "projects": projects,
                "error": extract_error_message(exc),
                "form_data": {
                    "title": title,
                    "description": description,
                    "due_date": due_date,
                    "project_id": int(project_id) if project_id.isdigit() else "",
                    "status": status,
                },
            },
            status_code=400,
        )

    return RedirectResponse(url=f"/todos/{todo_id}", status_code=303)


@router.post("/{todo_id}/status")
def change_todo_status(
    todo_id: int,
    status: str = Form(...),
    next_url: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    todo_service.change_status(db, todo_id, status, current_user)
    redirect_to = safe_next_url(next_url, default=f"/todos/{todo_id}")
    return RedirectResponse(url=redirect_to, status_code=303)


@router.post("/{todo_id}/delete")
def delete_todo(
    todo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    todo = todo_service.get_todo(db, todo_id)
    project_id = todo.project_id
    todo_service.delete_todo(db, todo_id, current_user)
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)
