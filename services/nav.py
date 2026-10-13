
"""Навигационный сервис: вход в модуль и возврат в главное меню.

Единый интерфейс — все хендлеры вызывают эти функции.
"""
from __future__ import annotations

from aiogram.types import FSInputFile, Message

from keyboards.main_menu import build_main_menu
from keyboards.module_menus import build_module_menu
from services.header_card import generate_card


async def enter_module(
    message: Message,
    module: str,
    text: str,
    *,
    couple=None,
) -> None:
    """Отправляет PNG-карточку + текст + контекстное меню модуля."""
    # 1. Карточка-заголовок
    card_path = generate_card(module)
    await message.answer_photo(
        FSInputFile(card_path),
        caption=None,
    )
    # 2. Текст + контекстное ReplyKeyboard
    await message.answer(
        text,
        reply_markup=build_module_menu(module),
    )


async def go_home(message: Message, couple=None) -> None:
    """Возвращает главное меню (ReplyKeyboard с 12 модулями)."""
    settings = couple.settings if couple else None
    paired = couple is not None
    kb = build_main_menu(settings, paired=paired)
    await message.answer("🏠 Главное меню", reply_markup=kb)
