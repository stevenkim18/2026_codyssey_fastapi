from sqlalchemy.orm import Session

from models.todo import Todo


class TodoRepository:
    """SQLAlchemy Session을 통해 todos 테이블에 접근하는 저장소 계층."""

    def find_all(self, db: Session, keyword: str | None = None) -> list[Todo]:
        query = db.query(Todo)
        if keyword:
            query = query.filter(Todo.title.like(f"%{keyword}%"))
        return query.order_by(Todo.is_completed.asc(), Todo.created_at.desc()).all()

    def find_by_id(self, db: Session, todo_id: int) -> Todo | None:
        return db.query(Todo).filter(Todo.id == todo_id).first()

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
