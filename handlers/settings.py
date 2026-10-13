
from __future__ import annotations
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message
from database.repositories.couples import CouplesRepository
from database.repositories.users import UsersRepository
from keyboards.main_menu import MODULES
from services.card_service import CardService
from services.nav import enter_module
from middlewares.message_cleanup import mark_important
from utils import emoji as e
from utils.validators import is_valid_timezone

router = Router(name="settings")
NOT_PAIRED = "Сначала создайте пару 👉 /start"

class SettingsStates(StatesGroup):
    timezone = State()
    name = State()

async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    tz_line = f"Часовой пояс: <b>{user.timezone}</b>" if couple else "Вы пока не в паре"
    await enter_module(message, "settings", tz_line, couple=couple)

async def handle_action(message: Message, action: str, session, user, couple, settings, language: str, state: FSMContext = None) -> None:
    if action == "modules":
        if couple is None:
            await message.answer(NOT_PAIRED)
            return
        modules = (couple.settings or {}).get("modules", {})
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"{'✅' if modules.get(code, True) else '⛔'} {MODULES[code].split(' ',1)[1]}", callback_data=f"settings:toggle:{code}")] for code in MODULES if code != "settings"])
        await message.answer(f"{e.GAME} Включённые модули:", reply_markup=kb)
    elif action == "tz":
        if state: await state.set_state(SettingsStates.timezone)
        await message.answer(f"{e.CLOCK} Введи часовой пояс (IANA), например: <code>Europe/Moscow</code>")
    elif action == "name":
        if couple is None:
            await message.answer(NOT_PAIRED)
            return
        if state: await state.set_state(SettingsStates.name)
        await message.answer(f"{e.EDIT} Как назвать вашу пару?")
    elif action == "profile":
        if couple is None:
            await message.answer(NOT_PAIRED)
            return
        await message.answer_chat_action("upload_photo")
        path = await CardService().profile_card(session, couple)
        msg = await message.answer_photo(FSInputFile(path), caption=f"{e.COUPLE} Профиль пары")
        await mark_important(msg.message_id)

@router.callback_query(F.data.startswith("settings:toggle:"))
async def settings_toggle(callback: CallbackQuery, session, couple) -> None:
    if couple is None:
        await callback.answer(NOT_PAIRED)
        return
    code = callback.data.split(":")[2]
    couples = CouplesRepository(session)
    current = await couples.get_setting(couple, f"modules.{code}", default=True)
    await couples.set_setting(couple, f"modules.{code}", not current)
    await session.flush()
    modules = (couple.settings or {}).get("modules", {})
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"{'✅' if modules.get(c, True) else '⛔'} {MODULES[c].split(' ',1)[1]}", callback_data=f"settings:toggle:{c}")] for c in MODULES if c != "settings"])
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()

@router.message(SettingsStates.timezone)
async def settings_tz_input(message: Message, state: FSMContext, session, user) -> None:
    tz = message.text.strip()
    if not is_valid_timezone(tz):
        await message.answer(f"{e.CROSS} Неверный пояс. Пример: <code>Europe/Moscow</code>")
        return
    await state.clear()
    await UsersRepository(session).set_timezone(user.user_id, tz)
    await session.flush()
    await message.answer(f"{e.CHECK} Часовой пояс: <b>{tz}</b>")

@router.message(SettingsStates.name)
async def settings_name_input(message: Message, state: FSMContext, session, couple) -> None:
    if couple is None:
        await state.clear()
        await message.answer(NOT_PAIRED)
        return
    await state.clear()
    name = message.text.strip()[:128] or "Мы"
    await CouplesRepository(session).set_name(couple, name)
    await session.flush()
    await message.answer(f"{e.CHECK} Теперь вы — <b>{name}</b> ❤️")
