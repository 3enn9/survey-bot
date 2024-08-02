from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, \
    ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from database import orm_delete_post, orm_add_post, orm_get_meets, orm_get_meet
from filters import IsUser

router = Router(name=__name__)
router.message.filter(IsUser())
router.callback_query.filter(IsUser())


class Survey(StatesGroup):
    district = State()
    address = State()
    description = State()
    photo = State()
    phone = State()

    product_for_change = None


main_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [KeyboardButton(text='Связаться со мной')],
        [KeyboardButton(text='Написать обращение')],
        [KeyboardButton(text='Мероприятия и дворовые встречи')]
    ]
)


class MeetPaginationCallback(CallbackData, prefix="meet_page"):
    page: int


@router.message(Command(commands=['start']))
async def start_command(message: types.Message):
    await message.answer(text='Привет, выбери нужный пункт', reply_markup=main_keyboard)


@router.message(F.text == 'Связаться со мной')
async def write_me(message: types.Message):
    await message.answer('Напишите мне @irolmad')


@router.message(StateFilter(None), F.text == 'Написать обращение')
async def write_an_appeal(message: types.Message, state: FSMContext):
    await message.answer(text='Напишите район, в котором обнаружена проблема, чтобы отменить действия, напишите'
                              '"Отменить"', reply_markup=ReplyKeyboardRemove())
    await state.set_state(Survey.district)


@router.message(StateFilter('*'), Command("отменить"))
@router.message(StateFilter('*'), F.text.casefold() == "отменить")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    if Survey.product_for_change:
        Survey.product_for_change = None
    await state.clear()
    await message.answer("Действия отменены", reply_markup=main_keyboard)


@router.message(Survey.district, F.text)
async def write_an_appeal(message: types.Message, state: FSMContext):
    await state.update_data(district=message.text)
    await state.update_data(user_name=message.from_user.first_name)
    await message.answer(text='Напишите точный адрес')
    await state.set_state(Survey.address)


@router.message(Survey.address, F.text)
async def write_an_appeal(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer(text='Напишите подробности вашего обращения')
    await state.set_state(Survey.description)


@router.message(Survey.description, F.text)
async def write_an_appeal(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(text='Прикрепите фото проблемы для вашего обращения, если нет фото, напишите "Нет"')
    await state.set_state(Survey.photo)


@router.message(Survey.photo, F.photo)
async def write_an_appeal(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)  # Сохраняем ID фото
    # Создаем клавиатуру с кнопкой для запроса контакта
    contact_keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text='Отправить контакт', request_contact=True)]
        ]
    )
    await message.answer(text='Напишите ваш номер телефона для связи или отправьте контакт',
                         reply_markup=contact_keyboard)
    await state.set_state(Survey.phone)


@router.message(Survey.photo, F.text)
async def get_phone_number(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(photo='AgACAgIAAxkBAAIEKGaqhpQo9sEg--nJX_d-kHA0nFcGAAKm4jEbGH5YSWQYxK_hsNyhAQADAgADeQADNQQ')
    # Создаем клавиатуру с кнопкой для запроса контакта
    contact_keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text='Отправить контакт', request_contact=True)]
        ]
    )
    await message.answer(text='Напишите ваш номер телефона для связи или отправьте контакт',
                         reply_markup=contact_keyboard)
    await state.set_state(Survey.phone)


@router.message(Survey.phone, F.contact)
async def write_an_appeal(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(phone_number=str(message.contact.phone_number))
    await state.update_data(user_id=str(message.from_user.id))
    await message.answer(text='Ваше обращение принято', reply_markup=main_keyboard)
    data = await state.get_data()
    await orm_add_post(session, data)
    await state.clear()


@router.message(Survey.phone, F.text)
async def get_phone_number(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(phone_number=message.text)
    await state.update_data(user_id=str(message.from_user.id))
    data = await state.get_data()
    await orm_add_post(session, data)
    await message.answer(text='Ваше обращение принято', reply_markup=main_keyboard)
    await state.clear()


@router.message(F.text == 'Мероприятия и дворовые встречи')
async def list_meets(message: types.Message, session: AsyncSession):
    meets, has_next_page = await orm_get_meets(0, session)
    keyboard = create_meets_pagination_keyboard(meets, 0, has_next_page)
    await message.answer(text='Список мероприятий', reply_markup=keyboard)


def create_meets_pagination_keyboard(meets, page, has_next_page):
    keyboard = InlineKeyboardBuilder()
    for meet in meets:
        keyboard.add(InlineKeyboardButton(
            text=f"Дата: {meet.date}, Тема: {meet.topic}",
            callback_data=f"meet_{meet.id}_{page}"  # Если это кнопка для мероприятия, а не пагинации
        ))

    if page > 0:
        prev_page_callback = MeetPaginationCallback(page=page - 1)
        keyboard.add(InlineKeyboardButton(
            text="Назад",
            callback_data=prev_page_callback.pack()
        ))

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


@router.callback_query(F.data.startswith('meet_'))
async def show_meet(callback_query: types.CallbackQuery, session: AsyncSession):
    data = callback_query.data.split('_')
    meet_id = int(data[1])
    page = int(data[2])

    meet = await orm_get_meet(meet_id, session)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Назад к списку мероприятий', callback_data=f'list_meets_{page}')]
    ])

    await callback_query.message.edit_text(
        text=f'Дата: {meet.date}\nТема: {meet.topic}\nВремя: {meet.time}\nМесто: {meet.place}',
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith('list_meets_'))
async def list_meets_callback_handler(callback_query: types.CallbackQuery, session: AsyncSession):
    page = int(callback_query.data.split('_')[2])  # Извлекаем текущую страницу
    meets, has_next_page = await orm_get_meets(page, session)
    keyboard = create_meets_pagination_keyboard(meets, page, has_next_page)

    await callback_query.message.edit_text(
        text='Список мероприятий',
        reply_markup=keyboard
    )

@router.message()
async def common(message: types.Message):
    await message.answer(text=f'Я вас не понимаю\nВаш ID: {str(message.from_user.id)}')
