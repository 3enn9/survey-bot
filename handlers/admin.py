from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.filters.callback_data import CallbackData
from database.models import Appeals
from filters import IsAdmin
from database import orm_get_posts, orm_get_post, orm_delete_post

router = Router(name=__name__)
router.message.filter(IsAdmin())

PAGE_SIZE = 10


# Определяем структуру callback_data
class PaginationCallback(CallbackData, prefix="page"):
    page: int


# Функция для создания инлайн-кнопок для постов и кнопок "Назад" и "Следующая страница"
def create_pagination_keyboard(posts, page, has_next_page):
    keyboard = InlineKeyboardBuilder()
    for post in posts:
        keyboard.add(InlineKeyboardButton(
            text=f"{post.user_name}: {post.district}",
            callback_data=f"post_{post.id}"
        ))

    # Кнопка "Назад" (если не на первой странице)
    if page > 0:
        prev_page_callback = PaginationCallback(page=page - 1)
        keyboard.add(InlineKeyboardButton(
            text="Назад",
            callback_data=prev_page_callback.pack()
        ))

    # Кнопка "Следующая страница" (если есть следующая страница)
    if has_next_page:
        next_page_callback = PaginationCallback(page=page + 1)
        keyboard.add(InlineKeyboardButton(
            text="Следующая страница",
            callback_data=next_page_callback.pack()
        ))

    return keyboard.adjust(1).as_markup()


@router.callback_query(F.data == 'admin')
@router.message(Command(commands=['admin']))
async def admin_command(message: types.Message | types.CallbackQuery, session: AsyncSession, bot: Bot):
    posts, has_next_page = await get_posts(0, session)
    keyboard = create_pagination_keyboard(posts, 0, has_next_page)
    if isinstance(message, types.Message):
        await message.answer(text="Список обращений:", reply_markup=keyboard)
    else:
        await message.message.delete()
        await message.message.answer(text="Список обращений:", reply_markup=keyboard)


@router.callback_query(PaginationCallback.filter())
async def paginate_callback_handler(callback_query: types.CallbackQuery, callback_data: PaginationCallback,
                                    session: AsyncSession):
    page = callback_data.page
    posts, has_next_page = await get_posts(page, session)
    keyboard = create_pagination_keyboard(posts, page, has_next_page)

    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    await callback_query.answer()


async def get_posts(page: int, session: AsyncSession):
    offset = page * PAGE_SIZE
    query = select(Appeals).offset(offset).limit(PAGE_SIZE + 1)
    result = await session.execute(query)
    posts = result.scalars().all()

    has_next_page = len(posts) > PAGE_SIZE
    if has_next_page:
        posts = posts[:-1]  # Удаление последнего элемента, если есть следующая страница

    return posts, has_next_page


# async def send_posts(chat_id: int, page: int, session: AsyncSession, bot: Bot):
#     posts, has_next_page = await get_posts(page, session)
#     keyboard = create_pagination_keyboard(posts, page, has_next_page)
#     await bot.send_message(chat_id=chat_id, text="Список обращений:", reply_markup=keyboard)


@router.callback_query(F.data.startswith('post_'))
async def show_post(callback_query: types.CallbackQuery, session: AsyncSession):
    post_id = int(callback_query.data.split('_')[1])
    post = await orm_get_post(post_id, session)
    await callback_query.message.answer_photo(photo=post.photo, caption=f'Обращение от <a href="tg://user?id={post.user_id}">{post.user_name}</a>\n'
                                                                        f'Номер телефона: {post.phone_number}\n'
                                                                        f'Дата обращения: {str(post.created).split()[0]}\n'
                                                                        f'Район: {post.district}\nАдрес: {post.address}\n'
                                                                        f'Комменатрий: {post.description}', parse_mode='HTML',
                                              reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                  [InlineKeyboardButton(text='Удалить обращение', callback_data=f'del_{post.id}')],
                                                  [InlineKeyboardButton(text='Список обращений', callback_data='admin')]
                                              ]
                                              ))
    await callback_query.message.delete()


@router.callback_query(F.data.startswith('del_'))
async def delete_post(callback_query: types.CallbackQuery, session: AsyncSession):
    await orm_delete_post(id=int(callback_query.data.split('_')[1]), session=session)
    await callback_query.answer('Обращение удалено', show_alert=True)
    await callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Список обращений', callback_data='admin')]
        ]
    ))