from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu


def make_keyboard(menu, n_cols=2):
    buttons = []
    for item in list(menu.keys()):
        button = menu.get(item)
        buttons.append(InlineKeyboardButton(
            text=button.get("name"),
            callback_data=button.get("callback_data"),
            url=button.get("url")))
    menu = build_menu(buttons, n_cols=n_cols)
    return InlineKeyboardMarkup(menu)
