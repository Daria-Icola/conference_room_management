"""
    Telegram event handlers
"""
from telegram.ext import (
    Dispatcher, Filters,
    CommandHandler, MessageHandler,
    CallbackQueryHandler,
)

from dtb.settings import DEBUG
from tgbot.handlers.utils import error
from tgbot.handlers.menu import handlers as onboarding_handlers, manage_data
from tgbot.handlers.menu.actions import actions, menu
from tgbot.handlers.menu.handlers import Menu

menu = Menu(path_to_file="tgbot/handlers/menu/manage_data.yml")

from tgbot.main import bot


def setup_dispatcher(dp):
    """
    Adding handlers for events from Telegram
    """

    def add_menu(menu_data, key):
        for item in list(menu_data.get(key).keys()):
            dp.add_handler(CallbackQueryHandler(
                actions.get(key).get(item),
                pattern=f"^{menu_data.get(key).get(item).get('callback_data')}"))


    # button back
    dp.add_handler(CallbackQueryHandler(menu.main, pattern="BACK_MAIN_MENU_LVL"))

    ###booking_menu

    dp.add_handler(
        CallbackQueryHandler(menu.choose_monthday, pattern=f"^{manage_data.CHOOSE_WEEKDAY}"))

    dp.add_handler(
        CallbackQueryHandler(menu.choose_hours, pattern=r"^\d{2}\.\d{2}$"))

    dp.add_handler(
        CallbackQueryHandler(menu.choose_minutes, pattern=r"^\d{1,2}\:$"))

    dp.add_handler(
        CallbackQueryHandler(menu.choose_minutes_for_booking, pattern=r"^\:\d{2}$"))

    dp.add_handler(
        CallbackQueryHandler(menu.confirm_booking, pattern=r"^\d{2,3}$"))

    dp.add_handler(
        CallbackQueryHandler(menu.confirm_info, pattern=f"^{manage_data.CONFIRM}"))

    dp.add_handler(
        CallbackQueryHandler(menu.room_menu, pattern=f"^{manage_data.SEE_OR_CHOOSE}"))

    dp.add_handler(
        CallbackQueryHandler(menu.active_booking, pattern=f"^{manage_data.SEE_ACTIVE_BOOKING}"))


    dp.add_handler(
        CallbackQueryHandler(menu.delete_booking_info, pattern=f"^{manage_data.DELETE_BOOKING}"))

    dp.add_handler(
        CallbackQueryHandler(menu.delete_booking, pattern=r"^Номер:\s*\d+$"))



    # dp.add_handler(
    #     CallbackQueryHandler(menu.handle_page, pattern=f"^{manage_data.NEXT}")
    # )
    #
    # dp.add_handler(
    #     CallbackQueryHandler(menu.handle_page, pattern=f"^{manage_data.BACK}")
    # )

    dp.add_handler(
        CallbackQueryHandler(menu.room_menu, pattern="Кандинский"))
    dp.add_handler(
        CallbackQueryHandler(menu.room_menu, pattern="Пименов"))
    dp.add_handler(
        CallbackQueryHandler(menu.room_menu, pattern="Родченко 30"))
    dp.add_handler(
        CallbackQueryHandler(menu.room_menu, pattern="Любовь Попова"))

    # menu_data = onboarding_handlers.load_yaml('tgbot/handlers/menu/manage_data.yml')
    # print("MENU_DATA: ", menu_data)
    # for item in list(actions.keys()):
    #     add_menu(menu_data, item)

    # onboarding
    dp.add_handler(CommandHandler("start", onboarding_handlers.command_start))

    # handling errors
    dp.add_error_handler(error.send_stacktrace_to_tg_chat)

    # EXAMPLES FOR HANDLERS
    # dp.add_handler(MessageHandler(Filters.text, <function_handler>))
    # dp.add_handler(MessageHandler(
    #     Filters.document, <function_handler>,
    # ))
    # dp.add_handler(CallbackQueryHandler(<function_handler>, pattern="^r\d+_\d+"))
    # dp.add_handler(MessageHandler(
    #     Filters.chat(chat_id=int(TELEGRAM_FILESTORAGE_ID)),
    #     # & Filters.forwarded & (Filters.photo | Filters.video | Filters.animation),
    #     <function_handler>,
    # ))

    # main handler
    dp.add_handler(
        MessageHandler(Filters.regex(rf'^(/s)?.*'), onboarding_handlers.main_handler)
    )
    return dp


n_workers = 0 if DEBUG else 4
dispatcher = setup_dispatcher(Dispatcher(bot, update_queue=None, workers=n_workers, use_context=True))
