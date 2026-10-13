
from __future__ import annotations
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from database.repositories.shopping import ShoppingRepository
from services.nav import enter_module
from utils import emoji as e

router = Router(name="shopping")

class ShoppingStates(StatesGroup):
    item = State()

async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    repo = ShoppingRepository(session)
    items = await repo.list_active(couple.couple_id)
    if not items:
        text = "Список пуст. Нажмите ➕ Добавить 👇"
    else:
        lines = [f"<b>Покупки ({len(items)}):</b>\n"]
        for it in items:
            icon = "✅" if it.done else "⬜"
            lines.append(f"{icon} {it.item}")
        text = "\n".join(lines)
    await enter_module(message, "shopping", text, couple=couple)

async def handle_action(message: Message, action: str, session, user, couple, settings, language: str, state: FSMContext = None) -> None:
    repo = ShoppingRepository(session)
    if action == "add":
        if state: await state.set_state(ShoppingStates.item)
        await message.answer(f"{e.CART} Что добавить в список?")
    elif action == "list":
        await show_menu(message, session=session, user=user, couple=couple, settings=settings, language=language)
    elif action == "done":
        items = await repo.list_active(couple.couple_id)
        active = [i for i in items if not i.done]
        if not active:
            await message.answer("Все куплено!")
            return
        rows = [[InlineKeyboardButton(text=f"✅ {i.item[:30]}", callback_data=f"shop:toggle:{i.id}")] for i in active[:10]]
        await message.answer("Отметить как купленное:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    elif action == "delete":
        items = await repo.list_active(couple.couple_id)
        if not items:
            await message.answer("Список пуст.")
            return
        rows = [[InlineKeyboardButton(text=f"🗑 {i.item[:30]}", callback_data=f"shop:del:{i.id}")] for i in items[:10]]
        await message.answer("Удалить позицию:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@router.message(ShoppingStates.item)
async def shop_item(message: Message, state: FSMContext, session, user, couple) -> None:
    await state.clear()
    repo = ShoppingRepository(session)
    await repo.create(couple_id=couple.couple_id, item=message.text, category="other", added_by=user.user_id)
    await session.flush()
    await message.answer(f"{e.CHECK} Добавлено: <b>{message.text}</b>")

@router.callback_query(F.data.startswith("shop:toggle:"))
async def shop_toggle(callback: CallbackQuery, session, couple) -> None:
    item_id = int(callback.data.split(":")[2])
    repo = ShoppingRepository(session)
    item = await repo.get_by_id(couple.couple_id, item_id)
    if item: await repo.toggle(item); await session.flush()
    await callback.message.edit_text(f"{e.CHECK} Отмечено!")
    await callback.answer()

@router.callback_query(F.data.startswith("shop:del:"))
async def shop_del(callback: CallbackQuery, session, couple) -> None:
    item_id = int(callback.data.split(":")[2])
    repo = ShoppingRepository(session)
    item = await repo.get_by_id(couple.couple_id, item_id)
    if item: await repo.remove(item); await session.flush()
    await callback.message.edit_text(f"{e.CHECK} Удалено.")
    await callback.answer()
