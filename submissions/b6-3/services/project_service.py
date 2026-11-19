from sqlalchemy.orm import Session

from exceptions import BadRequestException, ForbiddenException, NotFoundException
from models.project import Project
from models.user import User
from repositories.project_repository import ProjectRepository
from schemas.project import PROJECT_STATUS_LABELS, ProjectCreate, ProjectUpdate


class ProjectService:
    """프로젝트 CRUD 및 상태 변경 비즈니스 로직."""

    def __init__(self, project_repository: ProjectRepository | None = None) -> None:
        self.project_repository = project_repository or ProjectRepository()

    def list_projects(
        self,
        db: Session,
        keyword: str | None = None,
        status: str | None = None,
        owner_id: int | None = None,
    ) -> list[Project]:
        cleaned_keyword = keyword.strip() if keyword else None
        valid_status = status if status in PROJECT_STATUS_LABELS else None
        return self.project_repository.find_all(
            db,
            keyword=cleaned_keyword,
            status=valid_status,
            owner_id=owner_id,
        )

    def get_project(self, db: Session, project_id: int) -> Project:
        project = self.project_repository.find_by_id(db, project_id)
        if project is None:
            raise NotFoundException(f"프로젝트(#{project_id})를 찾을 수 없습니다.")
        return project

    def create_project(self, db: Session, data: ProjectCreate, current_user: User) -> Project:
        project = Project(
            name=data.name,
            description=data.description,
            status="active",
            owner_id=current_user.id,
        )
        return self.project_repository.create(db, project)

    def update_project(
        self,
        db: Session,
        project_id: int,
        data: ProjectUpdate,
        current_user: User,
    ) -> Project:
        project = self.get_project(db, project_id)
        if project.owner_id != current_user.id:
            raise ForbiddenException("본인이 생성한 프로젝트만 수정할 수 있습니다.")

        project.name = data.name
        project.description = data.description
        project.status = data.status
        return self.project_repository.update(db, project)

    def change_status(
        self,
        db: Session,
        project_id: int,
        new_status: str,
        current_user: User,
    ) -> Project:
        if new_status not in PROJECT_STATUS_LABELS:
            raise BadRequestException("지원하지 않는 프로젝트 상태입니다.")

        project = self.get_project(db, project_id)
        if project.owner_id != current_user.id:
            raise ForbiddenException("본인이 생성한 프로젝트의 상태만 변경할 수 있습니다.")

        project.status = new_status
        return self.project_repository.update(db, project)

    def delete_project(self, db: Session, project_id: int, current_user: User) -> None:
        project = self.get_project(db, project_id)
        if project.owner_id != current_user.id:
            raise ForbiddenException("본인이 생성한 프로젝트만 삭제할 수 있습니다.")

        self.project_repository.delete(db, project)
