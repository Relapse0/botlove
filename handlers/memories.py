
from __future__ import annotations
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from database.repositories.memories import MemoriesRepository
from keyboards.builders import paginate
from services.nav import enter_module
from utils import emoji as e

router = Router(name="memories")

class MemoryStates(StatesGroup):
    content = State()

async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    repo = MemoriesRepository(session)
    count = await repo.count_for_couple(couple.couple_id)
    text = f"Сохранено моментов: <b>{count}</b>

Выберите действие:"
    await enter_module(message, "memories", text, couple=couple)

async def handle_action(message: Message, action: str, session, user, couple, settings, language: str, state: FSMContext = None) -> None:
    if action == "add":
        if state: await state.set_state(MemoryStates.content)
        await message.answer(f"{e.PHOTO} Опиши момент или вставь текст:")
    elif action == "random":
        repo = MemoriesRepository(session)
        m = await repo.get_random(couple.couple_id)
        if m is None:
            await message.answer("Пока пусто. Сохраните первый момент!")
        else:
            await message.answer(f"{e.PHOTO} <b>Вспомните</b> · {m.created_at:%d.%m.%Y}

{m.content}")
    elif action == "list":
        repo = MemoriesRepository(session)
        items = await repo.list_for_couple(couple.couple_id, limit=5, offset=0)
        if not items:
            await message.answer("Пока пусто.")
            return
        text = "

".join(f"{e.PHOTO} {m.created_at:%d.%m.%Y}
{m.content}" for m in items)
        kb = paginate(page=0, total=100, page_size=5, prefix="memory:list")
        await message.answer(text, reply_markup=kb)

@router.message(MemoryStates.content)
async def memory_content(message: Message, state: FSMContext, session, user, couple) -> None:
    await state.clear()
    repo = MemoriesRepository(session)
    await repo.create(couple_id=couple.couple_id, author_id=user.user_id, type="note", content=message.text)
    await session.flush()
    await message.answer(f"{e.CHECK} Момент сохранён! 🖼️")

@router.callback_query(F.data.startswith("memory:list:"))
async def memory_list(callback: CallbackQuery, session, couple) -> None:
    page = int(callback.data.split(":")[2])
    repo = MemoriesRepository(session)
    items = await repo.list_for_couple(couple.couple_id, limit=5, offset=page * 5)
    if not items:
        await callback.message.edit_text("Больше нет записей.")
        await callback.answer()
        return
    text = "

".join(f"{e.PHOTO} {m.created_at:%d.%m.%Y}
{m.content}" for m in items)
    kb = paginate(page=page, total=100, page_size=5, prefix="memory:list")
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
