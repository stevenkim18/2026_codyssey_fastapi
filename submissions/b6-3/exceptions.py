class AppException(Exception):
    """애플리케이션 전역 예외의 기본 클래스."""

    def __init__(self, status_code: int, title: str, detail: str) -> None:
        self.status_code = status_code
        self.title = title
        self.detail = detail
        super().__init__(detail)


class AuthRequiredException(AppException):
    """비로그인 사용자가 보호 경로에 접근했을 때 발생 (로그인 페이지로 리다이렉트)."""

    def __init__(
        self,
        next_url: str = "/projects",
        detail: str = "로그인이 필요한 페이지입니다.",
    ) -> None:
        self.next_url = next_url
        super().__init__(status_code=401, title="로그인이 필요합니다", detail=detail)


class ForbiddenException(AppException):
    """로그인은 했으나 타인의 리소스를 수정/삭제하려는 등 권한이 없을 때 발생."""

    def __init__(self, detail: str = "이 작업을 수행할 권한이 없습니다.") -> None:
        super().__init__(status_code=403, title="접근 권한이 없습니다", detail=detail)


class NotFoundException(AppException):
    """요청한 리소스(회원/프로젝트/할 일)가 DB에 없을 때 발생."""

    def __init__(self, detail: str = "요청하신 데이터를 찾을 수 없습니다.") -> None:
        super().__init__(status_code=404, title="찾을 수 없습니다", detail=detail)


class BadRequestException(AppException):
    """잘못된 상태 전이나 유효하지 않은 요청일 때 발생."""

    def __init__(self, detail: str = "잘못된 요청입니다.") -> None:
        super().__init__(status_code=400, title="잘못된 요청입니다", detail=detail)
