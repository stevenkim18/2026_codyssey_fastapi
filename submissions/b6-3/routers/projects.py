from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database import get_db
from exceptions import ForbiddenException
from models.user import User
from routers import extract_error_message, safe_next_url, templates
from schemas.project import ProjectCreate, ProjectUpdate
from services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])
project_service = ProjectService()


@router.get("", response_class=HTMLResponse)
def list_projects(
    request: Request,
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    mine: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    only_mine = mine == "true"
    projects = project_service.list_projects(
        db,
        keyword=q,
        status=status,
        owner_id=current_user.id if only_mine else None,
    )
    return templates.TemplateResponse(
        request=request,
        name="projects/list.html",
        context={
            "current_user": current_user,
            "projects": projects,
            "keyword": (q or "").strip(),
            "selected_status": status or "",
            "only_mine": only_mine,
        },
    )


@router.get("/new", response_class=HTMLResponse)
def new_project_form(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="projects/create.html",
        context={
            "current_user": current_user,
            "error": None,
            "form_data": {"name": "", "description": ""},
        },
    )


@router.post("", response_class=HTMLResponse)
def create_project(
    request: Request,
    name: str = Form(default=""),
    description: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = ProjectCreate(name=name, description=description)
    except (ValidationError, ValueError) as exc:
        return templates.TemplateResponse(
            request=request,
            name="projects/create.html",
            context={
                "current_user": current_user,
                "error": extract_error_message(exc),
                "form_data": {"name": name, "description": description},
            },
            status_code=400,
        )

    project = project_service.create_project(db, data, current_user)
    return RedirectResponse(url=f"/projects/{project.id}", status_code=303)


@router.get("/{project_id}", response_class=HTMLResponse)
def detail_project(
    request: Request,
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    project = project_service.get_project(db, project_id)
    return templates.TemplateResponse(
        request=request,
        name="projects/detail.html",
        context={
            "current_user": current_user,
            "project": project,
        },
    )


@router.get("/{project_id}/edit", response_class=HTMLResponse)
def edit_project_form(
    request: Request,
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    project = project_service.get_project(db, project_id)
    if project.owner_id != current_user.id:
        raise ForbiddenException("본인이 생성한 프로젝트만 수정할 수 있습니다.")

    return templates.TemplateResponse(
        request=request,
        name="projects/edit.html",
        context={
            "current_user": current_user,
            "project": project,
            "error": None,
            "form_data": {
                "name": project.name,
                "description": project.description or "",
                "status": project.status,
            },
        },
    )


@router.post("/{project_id}/edit", response_class=HTMLResponse)
def update_project(
    request: Request,
    project_id: int,
    name: str = Form(default=""),
    description: str = Form(default=""),
    status: str = Form(default="active"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = project_service.get_project(db, project_id)
    if project.owner_id != current_user.id:
        raise ForbiddenException("본인이 생성한 프로젝트만 수정할 수 있습니다.")

    try:
        data = ProjectUpdate(name=name, description=description, status=status)
    except (ValidationError, ValueError) as exc:
        return templates.TemplateResponse(
            request=request,
            name="projects/edit.html",
            context={
                "current_user": current_user,
                "project": project,
                "error": extract_error_message(exc),
                "form_data": {"name": name, "description": description, "status": status},
            },
            status_code=400,
        )

    project_service.update_project(db, project_id, data, current_user)
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)


@router.post("/{project_id}/status")
def change_project_status(
    project_id: int,
    status: str = Form(...),
    next_url: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project_service.change_status(db, project_id, status, current_user)
    redirect_to = safe_next_url(next_url, default=f"/projects/{project_id}")
    return RedirectResponse(url=redirect_to, status_code=303)


@router.post("/{project_id}/delete")
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project_service.delete_project(db, project_id, current_user)
    return RedirectResponse(url="/projects", status_code=303)
