from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButtonPollType, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

start_kb= ReplyKeyboardBuilder()

start_kb.add(
    KeyboardButton(text="Просмотр"),
    KeyboardButton(text="Добавить"),

    KeyboardButton(text="Убрать меню"),
)
start_kb.adjust(1,1,1)

del_kb = ReplyKeyboardRemove()