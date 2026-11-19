from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class SignupForm(BaseModel):
    username: str
    email: str
    password: str
    password_confirm: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2 or len(cleaned) > 30:
            raise ValueError("사용자 이름은 2~30자 사이로 입력해 주세요.")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
            raise ValueError("올바른 이메일 주소를 입력해 주세요.")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("비밀번호는 6자 이상이어야 합니다.")
        if len(value.encode("utf-8")) > 72:
            raise ValueError("비밀번호는 72바이트 이하로 입력해 주세요.")
        return value

    def check_password_match(self) -> None:
        if self.password != self.password_confirm:
            raise ValueError("비밀번호와 비밀번호 확인이 일치하지 않습니다.")


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    provider: str
    created_at: datetime
