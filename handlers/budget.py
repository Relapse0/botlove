
from __future__ import annotations
from decimal import Decimal
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message
from database.repositories.transactions import TransactionsRepository
from services.budget_service import BudgetService
from services.card_service import CardService
from services.gamification_service import GamificationService
from services.nav import enter_module
from middlewares.message_cleanup import mark_important
from utils import emoji as e
from utils.validators import parse_amount

router = Router(name="budget")
CATEGORIES = ["food","transport","home","health","fun","gifts","travel","other"]

class BudgetStates(StatesGroup):
    amount = State()
    comment = State()
    limit = State()

async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    svc = BudgetService(session)
    balance = await svc.month_total(couple.couple_id)
    limit_val = await svc.get_limit(couple.couple_id)
    lines = ["<b>Бюджет этого месяца:</b>
"]
    lines.append(f"💸 Потрачено: <b>{balance:.2f} ₽</b>")
    if limit_val:
        pct = min(100, int(balance / limit_val * 100))
        lines.append(f"🎯 Лимит: <b>{limit_val:.2f} ₽</b> ({pct}%)")
    await enter_module(message, "budget", "
".join(lines), couple=couple)

async def handle_action(message: Message, action: str, session, user, couple, settings, language: str, state: FSMContext = None) -> None:
    if action == "add":
        if state: await state.set_state(BudgetStates.amount)
        await message.answer(f"{e.WALLET} Введи сумму траты (например, 250.50):")
    elif action == "report":
        await message.answer_chat_action("upload_photo")
        path = await CardService().budget_card(session, couple)
        msg = await message.answer_photo(FSInputFile(path), caption=f"{e.CHART} Бюджет месяца")
        await mark_important(msg.message_id)
    elif action == "limit":
        if state: await state.set_state(BudgetStates.limit)
        await message.answer(f"{e.TARGET} Введи месячный лимит (0 — убрать):")
    elif action == "chart":
        await message.answer_chat_action("upload_photo")
        path = await CardService().mood_chart(session, couple)
        msg = await message.answer_photo(FSInputFile(path), caption=f"{e.CHART} График")
        await mark_important(msg.message_id)

@router.message(BudgetStates.amount)
async def budget_amount(message: Message, state: FSMContext) -> None:
    amount = parse_amount(message.text)
    if amount is None or amount <= 0:
        await message.answer(f"{e.CROSS} Введи корректную сумму.")
        return
    await state.update_data(amount=str(amount))
    await state.set_state(BudgetStates.comment)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{e.category(c)} {c}", callback_data=f"budget:cat:{c}") for c in CATEGORIES[:4]],
        [InlineKeyboardButton(text=f"{e.category(c)} {c}", callback_data=f"budget:cat:{c}") for c in CATEGORIES[4:]],
    ])
    await message.answer(f"{e.QUESTION} Выбери категорию:", reply_markup=kb)

@router.callback_query(F.data.startswith("budget:cat:"))
async def budget_category(callback: CallbackQuery, state: FSMContext, session, user, couple) -> None:
    category = callback.data.split(":")[2]
    data = await state.get_data()
    await state.clear()
    svc = BudgetService(session)
    await svc.add_transaction(couple_id=couple.couple_id, user_id=user.user_id, amount=Decimal(data["amount"]), category=category, comment=None)
    await GamificationService(session).add_points(couple_id=couple.couple_id, amount=2, reason="budget", user_id=user.user_id)
    await session.flush()
    await callback.message.edit_text(f"{e.CHECK} Трата записана!

{e.category(category)} {category}: <b>{data['amount']} ₽</b>", reply_markup=None)
    await callback.answer()

@router.message(BudgetStates.limit)
async def budget_limit_input(message: Message, state: FSMContext, session, couple) -> None:
    amount = parse_amount(message.text)
    if amount is None:
        await message.answer(f"{e.CROSS} Введи корректную сумму.")
        return
    await state.clear()
    await BudgetService(session).set_limit(couple.couple_id, amount)
    await session.flush()
    await message.answer(f"{e.CHECK} Лимит установлен: <b>{amount} ₽</b>")
