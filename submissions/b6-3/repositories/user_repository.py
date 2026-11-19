from sqlalchemy.orm import Session, joinedload

from models.project import Project
from models.todo import Todo
from models.user import User


class UserRepository:
    """회원(User) 테이블 데이터 접근 계층."""

    def find_by_id(self, db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    def find_by_id_with_relations(self, db: Session, user_id: int) -> User | None:
        return (
            db.query(User)
            .options(
                joinedload(User.projects).joinedload(Project.todos),
                joinedload(User.todos).joinedload(Todo.project),
            )
            .filter(User.id == user_id)
            .first()
        )

    def find_all_with_relations(self, db: Session) -> list[User]:
        return (
            db.query(User)
            .options(joinedload(User.projects), joinedload(User.todos))
            .order_by(User.created_at.asc())
            .all()
        )

    def find_by_username(self, db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()

    def find_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def find_by_provider_id(self, db: Session, provider: str, provider_id: str) -> User | None:
        return (
            db.query(User)
            .filter(User.provider == provider, User.provider_id == provider_id)
            .first()
        )

    def create(self, db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
