from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.project import Project
    from models.todo import Todo


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider: Mapped[str] = mapped_column(String(20), default="local", nullable=False)
    provider_id: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    # 부모(User) 삭제 시 자식(Project, Todo) 처리 정책:
    # 탈퇴한 회원이 소유한 프로젝트와 작성한 할 일이 소유자 없는 고아 데이터로 남지 않도록
    # cascade="all, delete-orphan"을 적용하여 데이터 정합성을 유지합니다.
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
        order_by="Project.created_at.desc()",
    )
    todos: Mapped[list["Todo"]] = relationship(
        "Todo",
        back_populates="author",
        cascade="all, delete-orphan",
        order_by="Todo.created_at.desc()",
    )
