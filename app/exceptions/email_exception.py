from fastapi import status

from app.exceptions.custom_exceptions import AppException


class EmailException(AppException):
    def __init__(self, msg: str):
        super().__init__(detail=msg, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
