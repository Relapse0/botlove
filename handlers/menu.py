
"""Маршрутизация кнопок главного меню и контекстных меню модулей."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from keyboards.main_menu import MODULES, build_main_menu
from keyboards.module_menus import BUTTON_ROUTES, HOME_BTN
from services.nav import enter_module, go_home

router = Router(name="menu")

# Импорты функций модулей
from handlers import achievements as _ach
from handlers import analytics    as _ana
from handlers import budget       as _bud
from handlers import dates        as _dat
from handlers import games        as _gam
from handlers import gratitude    as _gra
from handlers import memories     as _mem
from handlers import mood         as _moo
from handlers import reminders    as _rem
from handlers import romance      as _rom
from handlers import settings     as _set
from handlers import shopping     as _sho

# Коды модулей -> функции входа (show_menu)
MODULE_ENTRY = {
    "reminders":    _rem.show_menu,
    "shopping":     _sho.show_menu,
    "budget":       _bud.show_menu,
    "mood":         _moo.show_menu,
    "dates":        _dat.show_menu,
    "gratitude":    _gra.show_menu,
    "romance":      _rom.show_menu,
    "analytics":    _ana.show_menu,
    "memories":     _mem.show_menu,
    "games":        _gam.show_menu,
    "achievements": _ach.show_menu,
    "settings":     _set.show_menu,
}

# Коды модулей -> функции действий внутри (action handlers)
MODULE_ACTIONS = {
    "reminders":    _rem.handle_action,
    "shopping":     _sho.handle_action,
    "budget":       _bud.handle_action,
    "mood":         _moo.handle_action,
    "dates":        _dat.handle_action,
    "gratitude":    _gra.handle_action,
    "romance":      _rom.handle_action,
    "analytics":    _ana.handle_action,
    "memories":     _mem.handle_action,
    "games":        _gam.handle_action,
    "achievements": _ach.handle_action,
    "settings":     _set.handle_action,
}


@router.message(Command("menu"))
async def cmd_menu(message: Message, couple, settings) -> None:
    await go_home(message, couple)


@router.message(F.text == HOME_BTN)
async def btn_home(message: Message, couple, settings) -> None:
    """Кнопка «🏠 В меню» — возвращает главное меню."""
    await go_home(message, couple)


@router.message(F.text.in_(list(MODULES.values())))
async def route_module(
    message: Message, session, user, couple, settings, language: str
) -> None:
    """Нажата кнопка модуля главного меню — входим в модуль."""
    for code, label in MODULES.items():
        if message.text == label:
            func = MODULE_ENTRY.get(code)
            if func:
                await func(message, session=session, user=user,
                           couple=couple, settings=settings, language=language)
            return


@router.message(F.text.in_(list(BUTTON_ROUTES.keys())))
async def route_action(
    message: Message, session, user, couple, settings, language: str
) -> None:
    """Нажата кнопка контекстного меню модуля — вызываем нужный action."""
    route = BUTTON_ROUTES.get(message.text)
    if not route:
        return
    module, action = route
    func = MODULE_ACTIONS.get(module)
    if func:
        await func(message, action=action, session=session, user=user,
                   couple=couple, settings=settings, language=language)
