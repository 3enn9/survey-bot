from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.filters.callback_data import CallbackData
from database.models import Appeals, Meets
from filters import IsAdmin
from database import orm_get_posts, orm_get_post, orm_delete_post, orm_add_meet, orm_get_meets, orm_get_meet, \
    orm_delete_meet

router = Router(name=__name__)
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

photo_posts = "AgACAgIAAxkBAAIEKGaqhpQo9sEg--nJX_d-kHA0nFcGAAKm4jEbGH5YSWQYxK_hsNyhAQADAgADeQADNQQ"


class Meet(StatesGroup):
    date = State()
    topic = State()
    time = State()
    place = State()

    product_for_change = None


# Определяем структуру callback_data
class PaginationCallback(CallbackData, prefix="post_page"):
    page: int


class MeetPaginationCallback(CallbackData, prefix="meet_page"):
    page: int


# Функция для создания инлайн-кнопок для постов и кнопок "Назад" и "Следующая страница"
def create_pagination_keyboard(posts, page, has_next_page):
    keyboard = InlineKeyboardBuilder()
    for post in posts:
        keyboard.add(InlineKeyboardButton(
            text=f"{post.user_name}: {post.district}",
            callback_data=f"post_{post.id}_{page}"  # Сохраняем ID обращения и номер страницы
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


main_admin_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [KeyboardButton(text='Список обращений')],
        [KeyboardButton(text='Список мероприятий')],
        [KeyboardButton(text='Добавить мероприятие')]

    ]
)


@router.callback_query(F.data == 'admin')
@router.message(Command(commands=['start']))
async def admin_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(text="Админ меню", reply_markup=main_admin_keyboard)


@router.message(F.text == 'Список обращений')
async def list_survey(message: types.Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    posts, has_next_page = await orm_get_posts(0, session)
    keyboard = create_pagination_keyboard(posts, 0, has_next_page)
    await message.answer_photo(
        photo=photo_posts,
        caption='Список обращений', reply_markup=keyboard)


@router.message(F.text == 'Список мероприятий')
async def list_meets(message: types.Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    meets, has_next_page = await orm_get_meets(0, session)
    keyboard = create_meets_pagination_keyboard(meets, 0, has_next_page)
    await message.answer(text='Список мероприятий', reply_markup=keyboard)


@router.callback_query(PaginationCallback.filter())
async def paginate_callback_handler(callback_query: types.CallbackQuery, callback_data: PaginationCallback,
                                    session: AsyncSession):
    page = callback_data.page
    posts, has_next_page = await orm_get_posts(page, session)
    keyboard = create_pagination_keyboard(posts, page, has_next_page)

    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    await callback_query.answer()


@router.callback_query(F.data.startswith('post_'))
async def show_post(callback_query: types.CallbackQuery, session: AsyncSession):
    data = callback_query.data.split('_')
    post_id = int(data[1])  # ID обращения
    page = int(data[2])  # Текущая страница

    post = await orm_get_post(post_id, session)

    # Создаем клавиатуру для текущего обращения с кнопкой "Назад"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Удалить обращение', callback_data=f'del_{post.id}')],
        [InlineKeyboardButton(text='Назад к списку обращений', callback_data=f'list_posts_{page}')]
        # Передаем текущую страницу
    ])

    # Используем InputMediaPhoto для редактирования сообщения с фотографией
    media = InputMediaPhoto(
        media=post.photo,
        caption=f'Обращение от <a href="tg://user?id={post.user_id}">{post.user_name}</a>\n'
                f'Номер телефона: {post.phone_number}\n'
                f'Дата обращения: {str(post.created).split()[0]}\n'
                f'Район: {post.district}\nАдрес: {post.address}\n'
                f'Комментарий: {post.description}',
        parse_mode='HTML'
    )

    await callback_query.message.edit_media(media=media, reply_markup=keyboard)
    # await callback_query.answer()


@router.callback_query(F.data.startswith('list_posts_'))
async def list_posts_callback_handler(callback_query: types.CallbackQuery, session: AsyncSession):
    data = callback_query.data.split('_')
    page = int(data[2])  # Извлекаем текущую страницу

    posts, has_next_page = await orm_get_posts(page, session)
    keyboard = create_pagination_keyboard(posts, page, has_next_page)
    media = InputMediaPhoto(media=photo_posts, caption='Список обращений')

    await callback_query.message.edit_media(
        media=media,
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith('del_'))
async def delete_post(callback_query: types.CallbackQuery, session: AsyncSession):
    post_id = int(callback_query.data.split('_')[1])
    await orm_delete_post(id=post_id, session=session)
    await callback_query.answer('Обращение удалено', show_alert=True)

    posts, has_next_page = await orm_get_posts(0, session)
    keyboard = create_pagination_keyboard(posts, 0, has_next_page)
    media = InputMediaPhoto(media=photo_posts, caption="Список обращений")
    await callback_query.message.edit_media(media=media, reply_markup=keyboard)


@router.message(StateFilter(None), F.text == 'Добавить мероприятие')
async def write_date(message: types.Message, state: FSMContext):
    await message.answer(text='Напишите дату в формате ДД.ММ.ГГ, чтобы отменить действия напишите "Отменить"', reply_markup=ReplyKeyboardRemove())
    await state.set_state(Meet.date)


@router.message(StateFilter('*'), Command("отменить"))
@router.message(StateFilter('*'), F.text.casefold() == "отменить")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    if Meet.product_for_change:
        Meet.product_for_change = None
    await state.clear()
    await message.answer("Действия отменены", reply_markup=main_admin_keyboard)


@router.message(Meet.date, F.text)
async def write_topic(message: types.Message, state: FSMContext):
    await state.update_data(date=message.text)
    await message.answer(text='Напишите тему встречи')
    await state.set_state(Meet.topic)


@router.message(Meet.topic, F.text)
async def write_time(message: types.Message, state: FSMContext):
    await state.update_data(topic=message.text)
    await message.answer(text='Напишите время встречи')
    await state.set_state(Meet.time)


@router.message(Meet.time, F.text)
async def write_place(message: types.Message, state: FSMContext):
    await state.update_data(time=message.text)
    await message.answer(text='Напишите место встречи')
    await state.set_state(Meet.place)


@router.message(Meet.place, F.text)
async def write_done(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(place=message.text)
    await message.answer(text='Мероприятие добавлено', reply_markup=main_admin_keyboard)
    data = await state.get_data()
    await orm_add_meet(session, data)
    await state.clear()


def create_meets_pagination_keyboard(meets, page, has_next_page):
    keyboard = InlineKeyboardBuilder()
    for meet in meets:
        keyboard.add(InlineKeyboardButton(
            text=f"Дата: {meet.date}, Тема: {meet.topic}",
            callback_data=f"meet_{meet.id}_{page}"  # Добавляем текущую страницу в callback_data
        ))

    # Кнопка "Назад" (если не на первой странице)
    if page > 0:
        prev_page_callback = MeetPaginationCallback(page=page - 1)
        keyboard.add(InlineKeyboardButton(
            text="Назад",
            callback_data=prev_page_callback.pack()
        ))

    # Кнопка "Следующая страница" (если есть следующая страница)
    if has_next_page:
        next_page_callback = MeetPaginationCallback(page=page + 1)
        keyboard.add(InlineKeyboardButton(
            text="Следующая страница",
            callback_data=next_page_callback.pack()
        ))

    return keyboard.adjust(1).as_markup()


@router.callback_query(MeetPaginationCallback.filter())
async def paginate_meets_callback_handler(callback_query: types.CallbackQuery, callback_data: MeetPaginationCallback,
                                          session: AsyncSession):
    page = callback_data.page
    meets, has_next_page = await orm_get_meets(page, session)
    keyboard = create_meets_pagination_keyboard(meets, page, has_next_page)

    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    # await callback_query.answer()


@router.callback_query(F.data.startswith('meet_'))
async def show_meet(callback_query: types.CallbackQuery, session: AsyncSession):
    data = callback_query.data.split('_')
    meet_id = int(data[1])
    page = int(data[2])  # Извлекаем текущую страницу
    print(data)

    meet = await orm_get_meet(meet_id, session)

    # Создаем клавиатуру для текущего мероприятия с кнопкой "Назад"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Удалить мероприятие', callback_data=f'delmeet_{meet.id}')],
        [InlineKeyboardButton(text='Назад к списку мероприятий', callback_data=f'list_meets_{page}')]
        # Передаем текущую страницу
    ])

    await callback_query.message.edit_text(
        text=f'Дата: {meet.date}\nТема: {meet.topic}\nВремя: {meet.time}\nМесто: {meet.place}',
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith('delmeet_'))
async def delete_meet(callback_query: types.CallbackQuery, session: AsyncSession):
    await orm_delete_meet(id=int(callback_query.data.split('_')[1]), session=session)
    await callback_query.answer('Мероприятие удалено', show_alert=True)

    # Обновляем сообщение с новым списком мероприятий
    meets, has_next_page = await orm_get_meets(0, session)
    keyboard = create_meets_pagination_keyboard(meets, 0, has_next_page)
    await callback_query.message.edit_text('Список мероприятий', reply_markup=keyboard)


@router.callback_query(F.data.startswith('list_meets_'))
async def list_meets_callback_handler(callback_query: types.CallbackQuery, session: AsyncSession):
    page = int(callback_query.data.split('_')[2])  # Извлекаем текущую страницу
    meets, has_next_page = await orm_get_meets(page, session)
    keyboard = create_meets_pagination_keyboard(meets, page, has_next_page)

    await callback_query.message.edit_text(
        text='Список мероприятий',
        reply_markup=keyboard
    )
    await callback_query.answer()
