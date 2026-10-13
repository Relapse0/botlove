
from __future__ import annotations
import random
from aiogram import Router
from aiogram.types import Message
from services.nav import enter_module
from utils import emoji as e

router = Router(name="romance")

QUESTIONS = ["Что впервые привлекло тебя во мне?","Какое наше воспоминание ты переживаешь заново чаще всего?","Чему ты научился(ась) у меня?","Какой наш совместный день был идеальным?","Что ты хочешь попробовать вместе в этом году?"]
CHALLENGES = ["Приготовьте ужин вместе 🍝","Сходите на прогулку без телефонов 🌳","Сделайте друг другу комплименты 🤍","Посмотрите фильм, который выберет партнёр 🎬","Напишите друг другу письма от руки 💌"]
TRUTHS = ["Самое смешное, что ты обо мне думал(а) в начале?","Какой твой самый неловкий момент?","Что ты никогда не рассказывал(а) никому?"]
DARES = ["Спой куплет любимой песни 🎤","Изобрази партнёра 🤭","Расскажи анекдот 😄","Станцуй 10 секунд 💃"]

async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    await enter_module(message, "romance", "Выберите действие:", couple=couple)

async def handle_action(message: Message, action: str, session, user, couple, settings, language: str, **kw) -> None:
    if action == "question":
        await message.answer(f"{e.QUESTION} <b>Вопрос дня</b>

{random.choice(QUESTIONS)}")
    elif action == "challenge":
        await message.answer(f"{e.FIRE} <b>Челлендж дня</b>

{random.choice(CHALLENGES)}")
    elif action == "td":
        import random as rnd
        kind = rnd.choice(["truth", "dare"])
        if kind == "truth":
            await message.answer(f"🤍 <b>Правда</b>

{random.choice(TRUTHS)}")
        else:
            await message.answer(f"🎯 <b>Действие</b>

{random.choice(DARES)}")
    elif action == "signal":
        signals = ["❤️","🔥","😘","🤗","😉","🫶"]
        if couple:
            try:
                await message.bot.send_message(couple.partner_id(message.from_user.id), f"{random.choice(signals)} Партнёр отправил тебе сигнал!")
                await message.answer(f"{e.CHECK} Сигнал отправлен! {random.choice(signals)}")
            except Exception:
                await message.answer("Не удалось отправить сигнал.")
