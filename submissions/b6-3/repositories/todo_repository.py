from sqlalchemy.orm import Session, joinedload

from models.todo import Todo


class TodoRepository:
    """할 일(Todo) 테이블 데이터 접근 계층 (동적 필터링 쿼리 지원)."""

    def find_all(
        self,
        db: Session,
        keyword: str | None = None,
        status: str | None = None,
        project_id: int | None = None,
        author_id: int | None = None,
    ) -> list[Todo]:
        query = db.query(Todo).options(
            joinedload(Todo.project),
            joinedload(Todo.author),
        )
        if keyword:
            query = query.filter(Todo.title.like(f"%{keyword}%"))
        if status:
            query = query.filter(Todo.status == status)
        if project_id is not None:
            query = query.filter(Todo.project_id == project_id)
        if author_id is not None:
            query = query.filter(Todo.author_id == author_id)
        return query.order_by(Todo.created_at.desc()).all()

    def find_by_id(self, db: Session, todo_id: int) -> Todo | None:
        return (
            db.query(Todo)
            .options(
                joinedload(Todo.project),
                joinedload(Todo.author),
            )
            .filter(Todo.id == todo_id)
            .first()
        )

    def create(self, db: Session, todo: Todo) -> Todo:
        db.add(todo)
        db.commit()
        db.refresh(todo)
        return todo

    def update(self, db: Session, todo: Todo) -> Todo:
        db.commit()
        db.refresh(todo)
        return todo

    def delete(self, db: Session, todo: Todo) -> None:
        db.delete(todo)
        db.commit()
