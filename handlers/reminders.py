
from __future__ import annotations
from datetime import datetime, timezone
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from database.repositories.reminders import RemindersRepository
from services.reminder_service import REPEAT_LABELS, ReminderService
from services.nav import enter_module
from utils import emoji as e
from utils.helpers import human_date
from utils.validators import parse_date, parse_time

router = Router(name="reminders")

class ReminderStates(StatesGroup):
    text = State()
    datetime = State()
    repeat = State()
    notify = State()
    private = State()

async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    repo = RemindersRepository(session)
    items = await repo.list_visible_for(couple.couple_id, user.user_id, limit=10)
    lines = ["<b>Ваши напоминания:</b>\n"]
    if not items:
        lines.append("Пока пусто. Нажмите ➕ Создать 👇")
    for r in items:
        icon = "🔁" if r.repeat_rule != "once" else "🔔"
        lines.append(f"{icon} <b>{r.text}</b>\n   ⏰ {human_date(r.remind_at, user.timezone)} · {REPEAT_LABELS.get(r.repeat_rule, '')}")
    await enter_module(message, "reminders", "\n".join(lines), couple=couple)

async def handle_action(message: Message, action: str, session, user, couple, settings, language: str, state: FSMContext = None) -> None:
    if action == "create":
        if state: await state.set_state(ReminderStates.text)
        await message.answer(f"{e.EDIT} Что нужно напомнить?")
    elif action == "list":
        await show_menu(message, session=session, user=user, couple=couple, settings=settings, language=language)
    elif action in ("repeats", "delete"):
        repo = RemindersRepository(session)
        items = await repo.list_visible_for(couple.couple_id, user.user_id, limit=20)
        if not items:
            await message.answer("Нет напоминаний.")
            return
        rows = []
        for r in items:
            cb = f"rem:del:{r.id}" if action == "delete" else f"rem:rep:{r.id}"
            rows.append([InlineKeyboardButton(text=f"🗑 {r.text[:25]}" if action == "delete" else f"🔁 {r.text[:25]}", callback_data=cb)])
        await message.answer("Выберите напоминание:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@router.message(ReminderStates.text)
async def rem_text(message: Message, state: FSMContext) -> None:
    await state.update_data(text=message.text)
    await state.set_state(ReminderStates.datetime)
    await message.answer(f"{e.CLOCK} Когда? Формат: <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>")

@router.message(ReminderStates.datetime)
async def rem_datetime(message: Message, state: FSMContext, user) -> None:
    dt = _parse_reminder_dt(message.text, user.timezone)
    if dt is None:
        await message.answer(f"{e.CROSS} Не понял дату. Пример: <code>14.02 21:00</code>")
        return
    await state.update_data(remind_at=dt.isoformat())
    await state.set_state(ReminderStates.repeat)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔂 Один раз", callback_data="rem:rep:once"),
         InlineKeyboardButton(text="🔁 Ежедневно", callback_data="rem:rep:daily")],
        [InlineKeyboardButton(text="🗓️ Еженедельно", callback_data="rem:rep:weekly"),
         InlineKeyboardButton(text="📅 Ежемесячно", callback_data="rem:rep:monthly")],
    ])
    await message.answer(f"{e.BELL} Как часто повторять?", reply_markup=kb)

@router.callback_query(F.data.startswith("rem:rep:"))
async def rem_repeat(callback: CallbackQuery, state: FSMContext) -> None:
    rule = callback.data.split(":")[2]
    if rule in ("once", "daily", "weekly", "monthly"):
        await state.update_data(repeat_rule=rule)
        await state.set_state(ReminderStates.notify)
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="👥 Обоим", callback_data="rem:notify:1"), InlineKeyboardButton(text="🙋 Только мне", callback_data="rem:notify:0")]])
        await callback.message.edit_text(f"{e.BELL} Кого уведомлять?", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("rem:notify:"))
async def rem_notify(callback: CallbackQuery, state: FSMContext) -> None:
    notify_both = callback.data.split(":")[2] == "1"
    await state.update_data(notify_both=notify_both)
    await state.set_state(ReminderStates.private)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"{e.UNLOCK} Видно партнёру", callback_data="rem:priv:0"), InlineKeyboardButton(text=f"{e.LOCK} Приватное", callback_data="rem:priv:1")]])
    await callback.message.edit_text("Кто видит это напоминание?", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("rem:priv:"))
async def rem_private(callback: CallbackQuery, state: FSMContext, session, user, couple) -> None:
    private = callback.data.split(":")[2] == "1"
    data = await state.get_data()
    await state.clear()
    repo = RemindersRepository(session)
    reminder = await repo.create(couple_id=couple.couple_id, author_id=user.user_id, text=data["text"], remind_at=datetime.fromisoformat(data["remind_at"]), repeat_rule=data["repeat_rule"], notify_both=data["notify_both"], visible_to_partner=not private)
    ReminderService().schedule(reminder)
    await session.flush()
    await callback.message.edit_text(f"{e.CHECK} Напоминание создано!\n\n🔔 {reminder.text}\n⏰ {human_date(reminder.remind_at, user.timezone)}", reply_markup=None)
    await callback.answer()

@router.callback_query(F.data.startswith("rem:del:"))
async def rem_delete(callback: CallbackQuery, session) -> None:
    rid = int(callback.data.split(":")[2])
    repo = RemindersRepository(session)
    reminder = await repo.get_by_id(rid)
    if reminder:
        ReminderService(callback.message.bot).unschedule(reminder)
        await repo.delete(reminder)
        await session.flush()
        await callback.message.edit_text(f"{e.CHECK} Напоминание удалено.")
    await callback.answer()

def _parse_reminder_dt(text, tz):
    from datetime import timedelta
    from zoneinfo import ZoneInfo
    try: zone = ZoneInfo(tz)
    except Exception: zone = timezone.utc
    parts = text.strip().split()
    now = datetime.now(zone)
    if len(parts) == 1:
        t = parse_time(parts[0])
        if not t: return None
        dt = now.replace(hour=t[0], minute=t[1], second=0, microsecond=0)
    elif len(parts) >= 2:
        t = parse_time(parts[-1])
        d = parse_date(parts[0], year=now.year)
        if not t or not d: return None
        dt = datetime(d.year, d.month, d.day, t[0], t[1], tzinfo=zone)
    else:
        return None
    if dt <= now: dt = dt + timedelta(days=1)
    return dt
