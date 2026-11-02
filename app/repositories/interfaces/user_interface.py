from abc import ABC, abstractmethod
from app.models.user import User


class UserInterface(ABC):

    @abstractmethod
    async def register_user(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    async def get_user_by_phone(self, phone: str) -> User | None:
        pass
