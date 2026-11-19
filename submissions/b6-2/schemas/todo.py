from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator


class TodoCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: date | None = None

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
    is_completed: bool = False


class TodoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    is_completed: bool
    due_date: date | None
    created_at: datetime
