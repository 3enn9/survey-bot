from aiogram import types
from aiogram.filters import BaseFilter


class IsAdmin(BaseFilter):
    def __init__(self):
        pass

    async def __call__(self, event: types.Message | types.CallbackQuery) -> bool:
        if isinstance(event, types.Message):
            return event.from_user.id == 877804669
        elif isinstance(event, types.CallbackQuery):
            return event.from_user.id == 877804669
        return False
