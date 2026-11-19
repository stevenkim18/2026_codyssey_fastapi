import re

from sqlalchemy.orm import Session

from auth.security import hash_password, verify_password
from exceptions import NotFoundException
from models.user import User
from repositories.user_repository import UserRepository
from schemas.auth import SignupForm


class AuthService:
    """회원가입, 로그인, Google OAuth 회원 연동 및 회원 조회를 담당합니다."""

    def __init__(self, user_repository: UserRepository | None = None) -> None:
        self.user_repository = user_repository or UserRepository()

    def authenticate(self, db: Session, identifier: str, password: str) -> User | None:
        cleaned = identifier.strip()
        if not cleaned or not password:
            return None

        user = self.user_repository.find_by_username(db, cleaned)
        if user is None:
            user = self.user_repository.find_by_email(db, cleaned.lower())
        if user is None:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    def signup(self, db: Session, form: SignupForm) -> User:
        form.check_password_match()

        if self.user_repository.find_by_username(db, form.username):
            raise ValueError("이미 사용 중인 사용자 이름입니다.")
        if self.user_repository.find_by_email(db, form.email):
            raise ValueError("이미 가입된 이메일 주소입니다.")

        new_user = User(
            username=form.username,
            email=form.email,
            password_hash=hash_password(form.password),
            provider="local",
        )
        return self.user_repository.create(db, new_user)

    def get_or_create_google_user(
        self,
        db: Session,
        google_id: str,
        email: str,
        name: str | None = None,
    ) -> User:
        existing = self.user_repository.find_by_provider_id(db, "google", google_id)
        if existing is not None:
            return existing

        normalized_email = email.strip().lower()
        by_email = self.user_repository.find_by_email(db, normalized_email)
        if by_email is not None:
            return by_email

        base_name = (name or normalized_email.split("@")[0]).strip()
        base_name = re.sub(r"\s+", "_", base_name)[:24] or "google_user"
        candidate = base_name
        suffix = 1
        while self.user_repository.find_by_username(db, candidate) is not None:
            candidate = f"{base_name}_{suffix}"
            suffix += 1

        new_user = User(
            username=candidate,
            email=normalized_email,
            password_hash=None,
            provider="google",
            provider_id=google_id,
        )
        return self.user_repository.create(db, new_user)

    def list_users(self, db: Session) -> list[User]:
        return self.user_repository.find_all_with_relations(db)

    def get_user_detail(self, db: Session, user_id: int) -> User:
        user = self.user_repository.find_by_id_with_relations(db, user_id)
        if user is None:
            raise NotFoundException(f"회원(#{user_id})을 찾을 수 없습니다.")
        return user
