from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup


class InlineMarkup:
    @classmethod
    def main_user_menu(cls):
        return types.InlineKeyboardMarkup(
            row_width=1,
            keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="Исторические данные", callback_data="history"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="Установить рабочие дни", callback_data="calendar"
                    )
                ]
            ]
        )

    @classmethod
    def select_market(cls):
        return types.InlineKeyboardMarkup(
            row_width=1,
            keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="EQ", callback_data="eq"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="FO", callback_data="fo"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="FX", callback_data="fx"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="назад", callback_data="back_to_main_menu"
                    )
                ]
            ]
        )

    @classmethod
    def eq_endpoints(cls):
        return types.InlineKeyboardMarkup(
            row_width=1,
            keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="tradestats", callback_data="tradestats_eq"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="orderstats", callback_data="orderstats_eq"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="obstats", callback_data="obstats_eq"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="hi2", callback_data="hi2_eq"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="назад", callback_data="back_to_select_market"
                    )
                ]
            ]
        )

    @classmethod
    def fx_endpoints(cls):
        return types.InlineKeyboardMarkup(
            row_width=1,
            keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="tradestats", callback_data="tradestats_fx"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="orderstats", callback_data="orderstats_fx"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="obstats", callback_data="obstats_fx"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="hi2", callback_data="hi2_fx"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="назад", callback_data="back_to_select_market"
                    )
                ]
            ]
        )

    @classmethod
    def fo_endpoints(cls):
        return types.InlineKeyboardMarkup(
            row_width=1,
            keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="tradestats", callback_data="tradestats_fo"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="obstats", callback_data="obstats_fo"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="hi2", callback_data="hi2_fo"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="futoi", callback_data="futoi_fo"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="назад", callback_data="back_to_select_market"
                    )
                ]
            ]
        )
