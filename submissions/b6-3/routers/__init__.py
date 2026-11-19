from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from config import BASE_DIR
from schemas.project import PROJECT_STATUS_LABELS
from schemas.todo import TODO_STATUS_LABELS

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["PROJECT_STATUS_LABELS"] = PROJECT_STATUS_LABELS
templates.env.globals["TODO_STATUS_LABELS"] = TODO_STATUS_LABELS


def extract_error_message(exc: ValidationError | ValueError) -> str:
    if isinstance(exc, ValidationError):
        first_error = exc.errors()[0]
        msg = str(first_error.get("msg", "입력값을 다시 확인해 주세요."))
        return msg.removeprefix("Value error, ")
    return str(exc)


def safe_next_url(next_url: str | None, default: str = "/projects") -> str:
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return default
