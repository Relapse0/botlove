
from __future__ import annotations
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from services.gamification_service import GamificationService
from services.nav import enter_module
from utils import emoji as e
from utils.helpers import progress_bar

router = Router(name="achievements")

async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    svc = GamificationService(session)
    points = await svc.balance(couple.couple_id)
    level, in_level, _ = await svc.level(couple.couple_id)
    text = f"{e.level(level)} <b>Уровень {level}</b>

Очков: <b>{points}</b>
{progress_bar(in_level, length=10)}"
    await enter_module(message, "achievements", text, couple=couple)

async def handle_action(message: Message, action: str, session, user, couple, settings, language: str, **kw) -> None:
    svc = GamificationService(session)
    if action == "list":
        items = await svc.list_achievements(couple.couple_id)
        lines = [f"{e.TROPHY} <b>Достижения</b>
"]
        for it in items:
            icon = "✅" if it["unlocked"] else "🔒"
            lines.append(f"{icon} <b>{it['title']}</b> — {it['desc']}")
        await message.answer("
".join(lines))
    elif action == "balance":
        points = await svc.balance(couple.couple_id)
        level, in_level, _ = await svc.level(couple.couple_id)
        bar = progress_bar(in_level, length=10)
        await message.answer(f"{e.level(level)} <b>Уровень {level}</b>

Очков: <b>{points}</b>
До следующего: {bar}")
