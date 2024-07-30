from aiogram import types, Bot
from aiogram.filters import BaseFilter, Filter


class IsAdmin(Filter):
    def __init__(self):
        pass

    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id == 877804669
