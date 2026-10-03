class AppError(Exception):
    status_code = 400
    detail = "Something went wrong"

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = 404
    detail = "Resource not found"


class AlreadyExistsError(AppError):
    status_code = 400
    detail = "Resource already exists"


class InvalidCredentialsError(AppError):
    status_code = 401
    detail = "Invalid credentials"
