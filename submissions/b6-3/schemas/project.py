from pydantic import BaseModel, field_validator

PROJECT_STATUS_LABELS: dict[str, str] = {
    "active": "진행 중",
    "completed": "완료",
    "archived": "보관",
}


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("프로젝트 이름은 필수 입력 항목입니다.")
        if len(cleaned) > 100:
            raise ValueError("프로젝트 이름은 100자 이내로 입력해 주세요.")
        return cleaned

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned if cleaned else None


class ProjectUpdate(ProjectCreate):
    status: str = "active"

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in PROJECT_STATUS_LABELS:
            raise ValueError("올바르지 않은 프로젝트 상태입니다.")
        return value
