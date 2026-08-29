from aiogram import Router

from bot.handlers import admin, catalog, menu, payments, profile, start, wallet

main_router = Router(name="main")
main_router.include_router(start.router)
main_router.include_router(menu.router)
main_router.include_router(wallet.router)
main_router.include_router(catalog.router)
main_router.include_router(payments.router)
main_router.include_router(admin.router)
main_router.include_router(profile.router)
