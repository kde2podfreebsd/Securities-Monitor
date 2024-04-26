from dotenv import load_dotenv
from telebot import types

load_dotenv()


class TextMarkup:

    _menu_text: str = None

    @classmethod
    @property
    def menu(cls):
        cls._menu_text = "Menu"
        return cls._menu_text


class InlineMarkup:
    _hide_menu: types.ReplyKeyboardRemove = None

    @classmethod
    @property
    def hide_reply_markup(cls) -> types.ReplyKeyboardRemove():
        cls._hide_menu: object = types.ReplyKeyboardRemove()
        return cls._hide_menu

    @classmethod
    def menu(cls):
        return types.InlineKeyboardMarkup(
            row_width=1,
            keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="⌛️ Delay's", callback_data="delay"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="📊 Reports", callback_data="report"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="⚙️ Config", callback_data="config"
                    )
                ],
            ],
        )

    @classmethod
    def delay_menu(cls):
        return types.InlineKeyboardMarkup(
            row_width=1,
            keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="", callback_data="delay"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="", callback_data="report"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="", callback_data="config"
                    )
                ],
            ],
        )
