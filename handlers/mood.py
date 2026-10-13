
from __future__ import annotations
from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message
from database.repositories.moods import MoodsRepository
from keyboards.inline import mood_keyboard
from services.card_service import CardService
from services.mood_service import MoodService, mood_alert_text
from services.nav import enter_module
from middlewares.message_cleanup import mark_important
from utils import emoji as e

router = Router(name="mood")

async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    repo = MoodsRepository(session)
    last = await repo.get_today(user.user_id)
    text = "Как ты себя чувствуешь сегодня?\n"
    if last:
        text = f"Сегодня ты отметил(а): {e.mood(last.value)}/5\n\nХочешь обновить?"
    await enter_module(message, "mood", text, couple=couple)

async def handle_action(message: Message, action: str, session, user, couple, settings, language: str, **kw) -> None:
    if action == "ask":
        await message.answer(f"{e.MOOD} Как твоё настроение?", reply_markup=mood_keyboard())
    elif action == "history":
        repo = MoodsRepository(session)
        items = await repo.list_for_user(user.user_id, limit=7)
        if not items:
            await message.answer("Нет записей.")
            return
        lines = ["<b>История за 7 записей:</b>\n"]
        for m in items:
            lines.append(f"{m.created_at:%d.%m} — {e.mood(m.value)} {m.value}/5")
        await message.answer("\n".join(lines))
    elif action == "chart":
        await message.answer_chat_action("upload_photo")
        path = await CardService().mood_chart(session, couple)
        msg = await message.answer_photo(FSInputFile(path), caption=f"{e.CHART} Настроение за 30 отметок")
        await mark_important(msg.message_id)

@router.callback_query(F.data.startswith("mood:"))
async def mood_choose(callback: CallbackQuery, session, user, couple) -> None:
    value = callback.data.split(":")[1]
    if value == "skip":
        await callback.message.edit_text(f"{e.INFO} Ок, пропускаем 🙂")
        await callback.answer()
        return
    if value == "chart":
        await callback.answer()
        await message_chat_action_and_photo(callback, session, couple)
        return
    mood_val = int(value)
    svc = MoodService(session)
    record, partner = await svc.save_mood(user, couple, mood_val, comment=None)
    await session.flush()
    await callback.message.edit_text(f"{e.mood(mood_val)} Записал! Настроение: <b>{mood_val}/5</b>", reply_markup=None)
    if partner:
        await callback.message.bot.send_message(partner.user_id, mood_alert_text(user))
    await callback.answer()

async def message_chat_action_and_photo(callback, session, couple):
    await callback.message.answer_chat_action("upload_photo")
    path = await CardService().mood_chart(session, couple)
    from aiogram.types import FSInputFile
    msg = await callback.message.answer_photo(FSInputFile(path), caption=f"{e.CHART} Настроение")
    await mark_important(msg.message_id)
