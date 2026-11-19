import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_dotenv_file(env_path: Path) -> None:
    """외부 패키지(python-dotenv) 없이 .env 파일을 안전하게 로드합니다."""
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


# submissions/b6-3/.env 우선 로드, 없으면 워크스페이스 루트 .env 참고
_load_dotenv_file(BASE_DIR / ".env")
_load_dotenv_file(BASE_DIR.parent.parent / ".env")

JWT_SECRET_KEY: str = os.getenv(
    "JWT_SECRET_KEY",
    "dev-only-change-this-secret-key-for-production-b6-3",
)
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "120"))
ACCESS_TOKEN_COOKIE_NAME: str = "access_token"
OAUTH_STATE_COOKIE_NAME: str = "google_oauth_state"

GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI: str = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "http://localhost:8000/auth/google/callback",
)

DB_PATH = BASE_DIR / "database.db"
DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"


def is_google_oauth_configured() -> bool:
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
