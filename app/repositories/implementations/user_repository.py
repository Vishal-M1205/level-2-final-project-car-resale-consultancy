import math

from sqlalchemy import and_, func, or_, select, update
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

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_users(
        self,
        page: int,
        limit: int,
        role: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        district: str | None = None,
        state: str | None = None,
        gender: str | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> dict:
        offset = (page - 1) * limit
        conditions = []
        if role:
            conditions.append(User.role == role.upper().strip())
        if is_active is not None:
            conditions.append(User.is_active == is_active)
        if search:
            term = f"%{search.strip()}%"
            conditions.append(
                or_(
                    User.name.ilike(term),
                    User.email.ilike(term),
                    User.phone.ilike(term),
                )
            )
        if name:
            conditions.append(User.name.ilike(f"%{name.strip()}%"))
        if email:
            conditions.append(User.email.ilike(f"%{email.strip()}%"))
        if phone:
            conditions.append(User.phone.ilike(f"%{phone.strip()}%"))
        if district:
            conditions.append(User.district.ilike(f"%{district.strip()}%"))
        if state:
            conditions.append(User.state.ilike(f"%{state.strip()}%"))
        if gender:
            conditions.append(User.gender == gender.upper().strip())

        where_clause = and_(*conditions) if conditions else True

        sort_column_map = {
            "created_at": User.created_at,
            "name": User.name,
            "email": User.email,
            "role": User.role,
        }
        sort_column = sort_column_map.get(sort_by, User.created_at)
        order_clause = sort_column.desc() if order == "desc" else sort_column.asc()

        stmnt = select(User).where(where_clause).order_by(order_clause).limit(limit).offset(offset)
        rows = await self.session.execute(stmnt)
        users = list(rows.scalars().all())

        count_stmnt = select(func.count()).select_from(User).where(where_clause)
        total_users = (await self.session.execute(count_stmnt)).scalar_one() or 0
        total_pages = math.ceil(total_users / limit) if total_users > 0 else 0

        return {
            "users": users,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "total_users": total_users,
        }

    async def soft_delete_user(self, user_id: int) -> User | None:
        stmnt = (
            update(User)
            .where(User.id == user_id)
            .values(is_active=False, updated_at=func.now())
            .returning(User)
        )
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, update_data: dict) -> User | None:
        update_data["updated_at"] = func.now()
        stmnt = update(User).where(User.id == user_id).values(**update_data).returning(User)
        result = await self.session.execute(stmnt)
        return result.scalar_one_or_none()
