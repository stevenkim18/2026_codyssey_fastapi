from sqlalchemy.orm import Session, joinedload

from models.project import Project
from models.todo import Todo


class ProjectRepository:
    """프로젝트(Project) 테이블 데이터 접근 계층."""

    def find_all(
        self,
        db: Session,
        keyword: str | None = None,
        status: str | None = None,
        owner_id: int | None = None,
    ) -> list[Project]:
        query = db.query(Project).options(
            joinedload(Project.owner),
            joinedload(Project.todos),
        )
        if keyword:
            query = query.filter(Project.name.like(f"%{keyword}%"))
        if status:
            query = query.filter(Project.status == status)
        if owner_id is not None:
            query = query.filter(Project.owner_id == owner_id)
        return query.order_by(Project.created_at.desc()).all()

    def find_by_id(self, db: Session, project_id: int) -> Project | None:
        return (
            db.query(Project)
            .options(
                joinedload(Project.owner),
                joinedload(Project.todos).joinedload(Todo.author),
            )
            .filter(Project.id == project_id)
            .first()
        )

    def create(self, db: Session, project: Project) -> Project:
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    def update(self, db: Session, project: Project) -> Project:
        db.commit()
        db.refresh(project)
        return project

    def delete(self, db: Session, project: Project) -> None:
        db.delete(project)
        db.commit()
