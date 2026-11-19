from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.todo import Todo
    from models.user import User


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 프로젝트 상태: active(진행 중) | completed(완료) | archived(보관)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    # N:1 양방향 연관관계 (Project -> User)
    owner: Mapped["User"] = relationship("User", back_populates="projects")

    # 1:N 양방향 연관관계 (Project -> Todo)
    # 부모(Project) 삭제 시 자식(Todo) 처리 정책:
    # 할 일은 반드시 특정 프로젝트에 소속되는 종속 엔티티이므로,
    # 프로젝트가 삭제되면 하위 할 일도 함께 삭제되도록 cascade="all, delete-orphan"을 적용합니다.
    todos: Mapped[list["Todo"]] = relationship(
        "Todo",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Todo.created_at.desc()",
    )
