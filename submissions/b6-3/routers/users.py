from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database import get_db
from models.user import User
from routers import templates
from services.auth_service import AuthService

router = APIRouter(prefix="/users", tags=["users"])
auth_service = AuthService()


@router.get("", response_class=HTMLResponse)
def list_users(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    users = auth_service.list_users(db)
    return templates.TemplateResponse(
        request=request,
        name="users/list.html",
        context={
            "current_user": current_user,
            "users": users,
        },
    )


@router.get("/{user_id}", response_class=HTMLResponse)
def detail_user(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    target_user = auth_service.get_user_detail(db, user_id)
    return templates.TemplateResponse(
        request=request,
        name="users/detail.html",
        context={
            "current_user": current_user,
            "target_user": target_user,
        },
    )
