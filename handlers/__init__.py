from aiogram import Router

from .users import router as user_router
from .admin import router as admin_router


router = Router(name=__name__)

router.include_routers(user_router, admin_router)