
from __future__ import annotations
from datetime import datetime, timezone
from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, FSInputFile, Message
from services.analytics_service import AnalyticsService
from services.card_service import CardService
from services.nav import enter_module
from middlewares.message_cleanup import mark_important
from utils import emoji as e

router = Router(name="analytics")

async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    await enter_module(message, "analytics", "Что показать?", couple=couple)

async def handle_action(message: Message, action: str, session, user, couple, settings, language: str, **kw) -> None:
    if action == "stats":
        await message.answer_chat_action("upload_photo")
        path = await CardService().stats_card(session, couple)
        msg = await message.answer_photo(FSInputFile(path), caption=f"{e.SPARKLES} Ваша пара в цифрах")
        await mark_important(msg.message_id)
    elif action == "mood":
        await message.answer_chat_action("upload_photo")
        path = await CardService().mood_chart(session, couple)
        msg = await message.answer_photo(FSInputFile(path), caption=f"{e.CHART} Настроение")
        await mark_important(msg.message_id)
    elif action == "wrapped":
        year = datetime.now(timezone.utc).year
        await message.answer_chat_action("upload_photo")
        path, _ = await CardService().wrapped_card(session, couple, year)
        text = await AnalyticsService(session).wrapped_text(couple, year)
        msg = await message.answer_photo(FSInputFile(path), caption=text)
        await mark_important(msg.message_id)
    elif action == "csv":
        buf = await AnalyticsService(session).export_transactions_csv(couple.couple_id)
        msg = await message.answer_document(BufferedInputFile(buf.getvalue(), filename="transactions.csv"), caption=f"{e.SCROLL} Экспорт трат")
        await mark_important(msg.message_id)
