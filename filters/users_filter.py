from aiogram import types
from aiogram.filters import BaseFilter


class IsUser(BaseFilter):
    def __init__(self):
        pass

    async def __call__(self, event: types.Message | types.CallbackQuery) -> bool:
        is_admin = await IsAdmin()(event)  # Проверка, является ли пользователь администратором
        return not is_admin
