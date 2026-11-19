from datetime import date

from sqlalchemy.orm import Session

from auth.security import hash_password
from models.project import Project
from models.todo import Todo
from models.user import User


def seed_initial_data(db: Session) -> None:
    """최초 실행 시 테스트 계정 2개와 연관된 프로젝트/할 일 샘플을 생성합니다."""
    if db.query(User).count() > 0:
        return

    demo_user = User(
        username="demo",
        email="demo@example.com",
        password_hash=hash_password("demo1234"),
        provider="local",
    )
    alice_user = User(
        username="alice",
        email="alice@example.com",
        password_hash=hash_password("alice1234"),
        provider="local",
    )
    db.add_all([demo_user, alice_user])
    db.flush()

    proj_backend = Project(
        name="FastAPI 인증·인가 고도화",
        description="JWT 기반 로그인, Depends 접근 제어, Google OAuth2 소셜 로그인을 통합하는 프로젝트입니다.",
        status="active",
        owner_id=demo_user.id,
    )
    proj_study = Project(
        name="SQLAlchemy 연관관계 스터디",
        description="User-Project-Todo 1:N 양방향 연관관계와 cascade 정책을 학습합니다.",
        status="completed",
        owner_id=alice_user.id,
    )
    db.add_all([proj_backend, proj_study])
    db.flush()

    todos = [
        Todo(
            title="JWT HttpOnly 쿠키 인증 흐름 검증하기",
            description="로그인 시 JWT 발급, 보호 경로 접근, 로그아웃 시 쿠키 삭제를 테스트합니다.",
            status="done",
            due_date=date(2026, 11, 22),
            project_id=proj_backend.id,
            author_id=demo_user.id,
        ),
        Todo(
            title="Google OAuth2 콜백 연동 확인하기",
            description="Google Cloud Console에서 Client ID/Secret을 발급받아 .env에 설정합니다.",
            status="in_progress",
            due_date=date(2026, 11, 26),
            project_id=proj_backend.id,
            author_id=demo_user.id,
        ),
        Todo(
            title="전역 예외 핸들러 401/403/404 동작 테스트",
            description="비로그인 접근, 타인 리소스 수정 시도, 없는 ID 접근 시 일관된 화면을 확인합니다.",
            status="todo",
            due_date=date(2026, 11, 29),
            project_id=proj_backend.id,
            author_id=alice_user.id,
        ),
        Todo(
            title="Project 삭제 시 하위 Todo cascade 정책 정리",
            description="cascade='all, delete-orphan' 선택 이유를 코드 주석과 README에 문서화합니다.",
            status="done",
            due_date=date(2026, 11, 21),
            project_id=proj_study.id,
            author_id=alice_user.id,
        ),
    ]
    db.add_all(todos)
    db.commit()
