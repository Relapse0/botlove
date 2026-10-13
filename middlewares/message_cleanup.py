"""Автоочистка сообщений бота.

Трекает ID последнего сообщения бота через TrackingBot.
Перед каждым апдейтом удаляет предыдущее сообщение (или убирает кнопки,
если сообщение старше 48 часов).
Сообщения, помеченные как важные (карточки статистики, отчёты),
НЕ удаляются — их ID хранится в отдельном ключе Redis.
"""
from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.methods import TelegramMethod
from aiogram.types import CallbackQuery, Message, TelegramObject

from database.redis import get_redis
from utils.logger import get_logger

log = get_logger("middleware.cleanup")

TTL = 60 * 60 * 48          # 48 часов — лимит Telegram на удаление
KEEP_TTL = 60 * 60 * 24 * 7 # 7 дней — важные сообщения
_mem: dict[int, tuple[int, float]] = {}  # chat_id -> (msg_id, unix_ts)
_keep: set[int] = set()                  # msg_id помеченных как важные


def _key(chat_id: int) -> str:
    return f"cleanup:last:{chat_id}"


def _keep_key(msg_id: int) -> str:
    return f"cleanup:keep:{msg_id}"


async def _get(chat_id: int) -> tuple[int, float] | None:
    """Возвращает (msg_id, unix_timestamp) или None."""
    r = get_redis()
    if r:
        v = await r.get(_key(chat_id))
        if v:
            parts = v.decode().split(":")
            return int(parts[0]), float(parts[1])
        return None
    return _mem.get(chat_id)


async def _set(chat_id: int, msg_id: int) -> None:
    r = get_redis()
    ts = time.time()
    if r:
        await r.set(_key(chat_id), f"{msg_id}:{ts}", ex=TTL)
    else:
        _mem[chat_id] = (msg_id, ts)


async def _clear(chat_id: int) -> None:
    r = get_redis()
    if r:
        await r.delete(_key(chat_id))
    else:
        _mem.pop(chat_id, None)


async def _is_kept(msg_id: int) -> bool:
    r = get_redis()
    if r:
        return bool(await r.exists(_keep_key(msg_id)))
    return msg_id in _keep


async def mark_important(msg_id: int) -> None:
    """Пометить сообщение как важное — оно НЕ будет удалено."""
    r = get_redis()
    if r:
        await r.set(_keep_key(msg_id), "1", ex=KEEP_TTL)
    else:
        _keep.add(msg_id)


def _get_chat_id(event: TelegramObject) -> int | None:
    if isinstance(event, Message):
        return event.chat.id
    if isinstance(event, CallbackQuery) and event.message:
        return event.message.chat.id
    return None


class TrackingBot(Bot):
    """Bot, который запоминает ID любого отправленного сообщения."""

    async def __call__(self, method: TelegramMethod, request_timeout=None):
        result = await super().__call__(method, request_timeout)
        # Отслеживаем все методы, возвращающие Message (send_message,
        # send_photo, send_document и т.д.)
        if isinstance(result, Message):
            await _set(result.chat.id, result.message_id)
        return result


class MessageCleanupMiddleware(BaseMiddleware):
    """Удаляет предыдущее сообщение бота перед обработкой апдейта."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        bot: Bot | None = data.get("bot")
        chat_id = _get_chat_id(event)

        if not chat_id or not bot:
            return await handler(event, data)

        entry = await _get(chat_id)
        if entry:
            last_id, ts = entry
            # Проверяем — не помечено ли сообщение как важное
            if not await _is_kept(last_id):
                age = time.time() - ts
                try:
                    if age < 60 * 60 * 47:  # младше ~47 ч — удаляем
                        await bot.delete_message(chat_id, last_id)
                    else:                   # старше — убираем кнопки
                        await bot.edit_message_reply_markup(
                            chat_id=chat_id,
                            message_id=last_id,
                            reply_markup=None,
                        )
                except Exception:
                    pass  # сообщение уже удалено или права нет — ок
            await _clear(chat_id)

        return await handler(event, data)
