from datetime import date

from sqlalchemy.orm import Session

from models.todo import Todo
from repositories.todo_repository import TodoRepository
from schemas.todo import TodoCreate, TodoResponse, TodoUpdate


class TodoService:
    """할 일 도메인의 비즈니스 로직과 ORM ↔ DTO 변환을 담당하는 서비스 계층."""

    def __init__(self, repository: TodoRepository | None = None) -> None:
        self.repository = repository or TodoRepository()

    @staticmethod
    def parse_due_date(due_date_str: str | None) -> date | None:
        if not due_date_str or not due_date_str.strip():
            return None
        try:
            return date.fromisoformat(due_date_str.strip())
        except ValueError as exc:
            raise ValueError("마감일 형식이 올바르지 않습니다. (예: YYYY-MM-DD)") from exc

    def get_todos(self, db: Session, keyword: str | None = None) -> list[TodoResponse]:
        cleaned_keyword = keyword.strip() if keyword else None
        todos = self.repository.find_all(db, keyword=cleaned_keyword)
        return [TodoResponse.model_validate(todo) for todo in todos]

    def get_summary(self, db: Session) -> dict[str, int]:
        todos = self.repository.find_all(db)
        total = len(todos)
        completed = sum(1 for todo in todos if todo.is_completed)
        return {
            "total": total,
            "completed": completed,
            "pending": total - completed,
        }

    def get_todo(self, db: Session, todo_id: int) -> TodoResponse | None:
        todo = self.repository.find_by_id(db, todo_id)
        if todo is None:
            return None
        return TodoResponse.model_validate(todo)

    def create_todo(self, db: Session, data: TodoCreate) -> TodoResponse:
        new_todo = Todo(
            title=data.title,
            description=data.description,
            due_date=data.due_date,
        )
        saved = self.repository.create(db, new_todo)
        return TodoResponse.model_validate(saved)

    def update_todo(self, db: Session, todo_id: int, data: TodoUpdate) -> TodoResponse | None:
        todo = self.repository.find_by_id(db, todo_id)
        if todo is None:
            return None

        todo.title = data.title
        todo.description = data.description
        todo.due_date = data.due_date
        todo.is_completed = data.is_completed

        updated = self.repository.update(db, todo)
        return TodoResponse.model_validate(updated)

    def toggle_todo(self, db: Session, todo_id: int) -> TodoResponse | None:
        todo = self.repository.find_by_id(db, todo_id)
        if todo is None:
            return None

        todo.is_completed = not todo.is_completed
        updated = self.repository.update(db, todo)
        return TodoResponse.model_validate(updated)

    def delete_todo(self, db: Session, todo_id: int) -> bool:
        todo = self.repository.find_by_id(db, todo_id)
        if todo is None:
            return False

        self.repository.delete(db, todo)
        return True
