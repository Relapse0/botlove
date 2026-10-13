
from __future__ import annotations
import random
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from database.repositories.couples import CouplesRepository
from services.gamification_service import GamificationService
from services.nav import enter_module
from utils import emoji as e

router = Router(name="games")

QUIZ = [("Какой язык любви у твоего партнёра?",["Слова","Время","Подарки","Забота"],1),("Что партнёр выберет на выходные?",["Горы","Море","Город","Диван"],3),("Любимый способ сказать «я тебя люблю»?",["Словами","Объятиями","Сюрпризом","Все сразу"],2)]

class QuizStates(StatesGroup):
    answering = State()

class GoalsStates(StatesGroup):
    title = State()

async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    await enter_module(message, "games", "Выберите игру:", couple=couple)

async def handle_action(message: Message, action: str, session, user, couple, settings, language: str, state: FSMContext = None) -> None:
    if action == "quiz":
        if state:
            await state.set_state(QuizStates.answering)
            await state.update_data(score=0, q=0)
        q, options, _ = QUIZ[0]
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=opt, callback_data=f"quiz:ans:0:{i}")] for i, opt in enumerate(options)])
        await message.answer(f"{e.QUESTION} Вопрос 1/{len(QUIZ)}\n\n{q}", reply_markup=kb)
    elif action == "duel":
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🗿", callback_data="duel:0"), InlineKeyboardButton(text="📄", callback_data="duel:1"), InlineKeyboardButton(text="✂️", callback_data="duel:2")]])
        await message.answer(f"{e.DICE} <b>Дуэль</b>\n\nВыбери жест:", reply_markup=kb)
    elif action == "goals":
        goals = (couple.settings or {}).get("goals", [])
        text = f"{e.TARGET} <b>Совместные цели</b>\n\n" + ("\n".join(f"• {g}" for g in goals) if goals else "Пока пусто.")
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"{e.PLUS} Добавить цель", callback_data="goals:add")]])
        await message.answer(text, reply_markup=kb)

@router.callback_query(QuizStates.answering, F.data.startswith("quiz:ans:"))
async def quiz_answer(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, q_str, choice_str = callback.data.split(":")
    q = int(q_str); choice = int(choice_str)
    data = await state.get_data()
    score = data.get("score", 0)
    if choice == QUIZ[q][2]: score += 1
    await state.update_data(score=score, q=q + 1)
    if q + 1 < len(QUIZ):
        nq, opts, _ = QUIZ[q + 1]
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=opt, callback_data=f"quiz:ans:{q+1}:{i}")] for i, opt in enumerate(opts)])
        await callback.message.edit_text(f"{e.QUESTION} Вопрос {q+2}/{len(QUIZ)}\n\n{nq}", reply_markup=kb)
    else:
        await state.clear()
        total = len(QUIZ)
        await callback.message.edit_text(f"{e.TROPHY} <b>Результат: {score}/{total}</b>\n\n{'😍 Вы знаете друг друга отлично!' if score==total else '🤍 Есть куда расти!'}")
    await callback.answer()

@router.callback_query(F.data.startswith("duel:"))
async def duel_play(callback: CallbackQuery, session, couple) -> None:
    you = int(callback.data.split(":")[1])
    bot_choice = random.randint(0, 2)
    names = ["🗿", "📄", "✂️"]
    diff = (you - bot_choice) % 3
    result = "Ничья 🤝" if diff == 0 else ("Ты победил(а)! 🎉" if diff == 1 else "Бот победил 🤖")
    points = 5 if diff == 1 else 1
    await GamificationService(session).add_points(couple_id=couple.couple_id, amount=points, reason="duel", user_id=callback.from_user.id)
    await session.flush()
    await callback.message.edit_text(f"Ты: {names[you]} · Бот: {names[bot_choice]}\n\n{result}\n+{points} очков")
    await callback.answer()

@router.callback_query(F.data == "goals:add")
async def goals_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GoalsStates.title)
    await callback.message.answer(f"{e.TARGET} Опишите цель:")
    await callback.answer()

@router.message(GoalsStates.title)
async def goals_title(message: Message, state: FSMContext, session, couple) -> None:
    await state.clear()
    couples = CouplesRepository(session)
    goals = list((couple.settings or {}).get("goals", []))
    goals.append(message.text)
    await couples.set_setting(couple, "goals", goals)
    await session.flush()
    await message.answer(f"{e.CHECK} Цель добавлена: <b>{message.text}</b>")
