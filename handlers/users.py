from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, \
    ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from database import orm_delete_post, orm_add_post

router = Router(name=__name__)


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


@router.message(Command(commands=['start']))
async def start_command(message: types.Message):
    await message.answer(text='Привет, выбери нужный пункт', reply_markup=main_keyboard)


@router.message(F.text == 'Связаться со мной')
async def write_me(message: types.Message):
    await message.answer('Напишите мне @irolmad')


@router.message(StateFilter(None), F.text == 'Написать обращение')
async def write_an_appeal(message: types.Message, state: FSMContext):
    await message.answer(text='Напишите район, в котором обнаружена проблема', reply_markup=ReplyKeyboardRemove())
    await state.set_state(Survey.district)

@router.message(StateFilter('*'), Command("отмена"))
@router.message(StateFilter('*'), F.text.casefold() == "отмена")
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
    await message.answer(text='Прикрепите фото проблемы для вашего обращения')
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
async def meets(message: types.Message):
    pass


@router.message()
async def common(message: types.Message):
    await message.answer(text=f'{str(message.from_user.id)} {message.photo[-1].file_id}')
