from datetime import date

from pydantic import BaseModel, field_validator

TODO_STATUS_LABELS: dict[str, str] = {
    "todo": "대기",
    "in_progress": "진행 중",
    "done": "완료",
}


class TodoCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: date | None = None
    project_id: int

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("할 일 제목은 필수 입력 항목입니다.")
        if len(cleaned) > 100:
            raise ValueError("할 일 제목은 100자 이내로 입력해 주세요.")
        return cleaned

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned if cleaned else None


class TodoUpdate(TodoCreate):
    status: str = "todo"

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in TODO_STATUS_LABELS:
            raise ValueError("올바르지 않은 할 일 상태입니다.")
        return value
