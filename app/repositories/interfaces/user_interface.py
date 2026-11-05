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

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> User | None:
        pass

    @abstractmethod
    async def get_users(
        self,
        page: int,
        limit: int,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> dict:
        pass

    @abstractmethod
    async def soft_delete_user(self, user_id: int) -> User | None:
        pass

    @abstractmethod
    async def update_user(self, user_id: int, update_data: dict) -> User | None:
        pass
