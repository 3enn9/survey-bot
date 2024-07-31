from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Appeals, Meets

PAGE_SIZE = 10


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


async def orm_get_posts(page: int, session: AsyncSession):
    offset = page * PAGE_SIZE
    query = select(Appeals).offset(offset).limit(PAGE_SIZE + 1)
    result = await session.execute(query)
    posts = result.scalars().all()

    has_next_page = len(posts) > PAGE_SIZE
    if has_next_page:
        posts = posts[:-1]  # Удаление последнего элемента, если есть следующая страница

    return posts, has_next_page


async def orm_get_post(post_id: int, session: AsyncSession):
    query = select(Appeals).where(Appeals.id == post_id)
    result = await session.execute(query)
    post = result.scalar_one_or_none()
    return post

async def orm_get_meet(post_id: int, session: AsyncSession):
    query = select(Meets).where(Meets.id == post_id)
    result = await session.execute(query)
    post = result.scalar_one_or_none()
    return post


async def orm_add_meet(session: AsyncSession, data: dict):
    obj = Meets(
        date=data['date'],
        topic=data['topic'],
        time=data['time'],
        place=data['place']
    )
    session.add(obj)
    await session.commit()


async def orm_get_meets(page: int, session: AsyncSession):
    offset = page * PAGE_SIZE
    query = select(Meets).offset(offset).limit(PAGE_SIZE + 1)
    result = await session.execute(query)
    meets = result.scalars().all()
    has_next_page = len(meets) > PAGE_SIZE
    if has_next_page:
        meets = meets[:-1]  # Удаление последнего элемента, если есть следующая страница

    return meets, has_next_page

async def orm_delete_meet(id: int, session: AsyncSession):
    query = delete(Meets).where(Appeals.id == id)
    await session.execute(query)
    await session.commit()