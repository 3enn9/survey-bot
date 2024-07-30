from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .models import Appeals


async def orm_add_post(session: AsyncSession, data: dict):
    obj = Appeals(
        user_id=data['user_id'],
        district=data['district'],
        address=data['address'],
        description=data['description'],
        photo=data['photo'],
        phone_number=data['phone_number'],
        user_name=data['user_name']
    )
    session.add(obj)
    await session.commit()


async def orm_delete_post(id: int, session: AsyncSession):
    query = delete(Appeals).where(Appeals.id == id)
    await session.execute(query)
    await session.commit()


async def orm_get_posts(session: AsyncSession):
    stmt = select(Appeals)
    result = await session.execute(stmt)
    posts = result.scalars().all()
    return posts


async def orm_get_post(post_id: int, session: AsyncSession):
    query = select(Appeals).where(Appeals.id == post_id)
    result = await session.execute(query)
    post = result.scalar_one_or_none()
    return post


# async def orm_delete_post(post_id: int, session: AsyncSession):
#     query = select(Appeals).where(Appeals.id == post_id)
#     result = await session.execute(query)
#     post = result.scalar_one_or_none()
#     if post:
#         await session.delete(post)
#         await session.commit()
