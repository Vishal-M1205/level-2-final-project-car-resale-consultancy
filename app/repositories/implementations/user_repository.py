from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.interfaces.user_interface import UserInterface


class UserRepository(UserInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_user(self, user: User):
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        print(user.id)

        return user

    async def get_user_by_email(self, email: str) -> User:
        stmnt = select(User).where(User.email == email)

        row = await self.session.execute(stmnt)

        row = row.scalar_one_or_none()

        return row

    async def get_user_by_phone(self, phone: str) -> User:
        stmnt = select(User).where(User.phone == phone)

        row = await self.session.execute(stmnt)

        row = row.scalar_one_or_none()

        return row
