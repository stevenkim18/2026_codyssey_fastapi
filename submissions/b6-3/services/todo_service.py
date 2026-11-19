from datetime import date

from sqlalchemy.orm import Session

from exceptions import BadRequestException, ForbiddenException, NotFoundException
from models.todo import Todo
from models.user import User
from repositories.project_repository import ProjectRepository
from repositories.todo_repository import TodoRepository
from schemas.todo import TODO_STATUS_LABELS, TodoCreate, TodoUpdate


class TodoService:
    """할 일 CRUD, 동적 필터링 및 상태 전이 비즈니스 로직."""

    def __init__(
        self,
        todo_repository: TodoRepository | None = None,
        project_repository: ProjectRepository | None = None,
    ) -> None:
        self.todo_repository = todo_repository or TodoRepository()
        self.project_repository = project_repository or ProjectRepository()

    @staticmethod
    def parse_due_date(due_date_str: str | None) -> date | None:
        if not due_date_str or not due_date_str.strip():
            return None
        try:
            return date.fromisoformat(due_date_str.strip())
        except ValueError as exc:
            raise ValueError("마감일 형식이 올바르지 않습니다. (예: YYYY-MM-DD)") from exc

    def list_todos(
        self,
        db: Session,
        keyword: str | None = None,
        status: str | None = None,
        project_id: int | None = None,
        author_id: int | None = None,
    ) -> list[Todo]:
        cleaned_keyword = keyword.strip() if keyword else None
        valid_status = status if status in TODO_STATUS_LABELS else None
        return self.todo_repository.find_all(
            db,
            keyword=cleaned_keyword,
            status=valid_status,
            project_id=project_id,
            author_id=author_id,
        )

    def get_todo(self, db: Session, todo_id: int) -> Todo:
        todo = self.todo_repository.find_by_id(db, todo_id)
        if todo is None:
            raise NotFoundException(f"할 일(#{todo_id})을 찾을 수 없습니다.")
        return todo

    def create_todo(self, db: Session, data: TodoCreate, current_user: User) -> Todo:
        project = self.project_repository.find_by_id(db, data.project_id)
        if project is None:
            raise ValueError("선택한 프로젝트가 존재하지 않습니다.")
        if project.status == "archived":
            raise ValueError("보관(Archived) 상태의 프로젝트에는 새 할 일을 추가할 수 없습니다.")

        new_todo = Todo(
            title=data.title,
            description=data.description,
            due_date=data.due_date,
            status="todo",
            project_id=project.id,
            author_id=current_user.id,
        )
        return self.todo_repository.create(db, new_todo)

    def update_todo(
        self,
        db: Session,
        todo_id: int,
        data: TodoUpdate,
        current_user: User,
    ) -> Todo:
        todo = self.get_todo(db, todo_id)
        if todo.author_id != current_user.id:
            raise ForbiddenException("본인이 작성한 할 일만 수정할 수 있습니다.")

        project = self.project_repository.find_by_id(db, data.project_id)
        if project is None:
            raise ValueError("선택한 프로젝트가 존재하지 않습니다.")

        todo.title = data.title
        todo.description = data.description
        todo.due_date = data.due_date
        todo.project_id = project.id
        todo.status = data.status
        return self.todo_repository.update(db, todo)

    def change_status(
        self,
        db: Session,
        todo_id: int,
        new_status: str,
        current_user: User,
    ) -> Todo:
        """할 일 상태 전이(대기 -> 진행 중 -> 완료). 작성자 또는 프로젝트 소유자만 변경 가능."""
        if new_status not in TODO_STATUS_LABELS:
            raise BadRequestException("지원하지 않는 할 일 상태입니다.")

        todo = self.get_todo(db, todo_id)
        is_allowed = (
            todo.author_id == current_user.id
            or todo.project.owner_id == current_user.id
        )
        if not is_allowed:
            raise ForbiddenException("할 일 작성자 또는 프로젝트 소유자만 상태를 변경할 수 있습니다.")

        todo.status = new_status
        return self.todo_repository.update(db, todo)

    def delete_todo(self, db: Session, todo_id: int, current_user: User) -> None:
        todo = self.get_todo(db, todo_id)
        if todo.author_id != current_user.id:
            raise ForbiddenException("본인이 작성한 할 일만 삭제할 수 있습니다.")

        self.todo_repository.delete(db, todo)
