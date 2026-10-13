"""Контекстные ReplyKeyboard-меню для каждого из 12 модулей.

Каждый модуль имеет своё меню с кнопками + «🏠 В меню».
Возвращает ReplyKeyboardMarkup — просто подставляй в reply_markup.
"""
from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

# Кнопка возврата — единая для всех модулей
HOME_BTN = "🏠 В меню"

# Меню каждого модуля: список строк (кнопок)
MODULE_BUTTONS: dict[str, list[list[str]]] = {
    "reminders": [
        ["➕ Создать", "📋 Список"],
        ["🔁 Повторы", "🗑 Удалить"],
    ],
    "shopping": [
        ["➕ Добавить", "📋 Список"],
        ["✅ Куплено", "🗑 Удалить"],
    ],
    "budget": [
        ["➕ Трата", "📊 Отчёт"],
        ["💰 Лимит", "📈 График"],
    ],
    "mood": [
        ["😊 Отметить", "📈 График"],
        ["📅 История"],
    ],
    "dates": [
        ["➕ Добавить", "📋 Список"],
        ["⏳ Обратный отсчёт", "💌 Капсула"],
    ],
    "gratitude": [
        ["💌 Сказать спасибо", "📜 Отчёт месяца"],
    ],
    "romance": [
        ["❓ Вопрос дня", "🔥 Челлендж"],
        ["🎲 Правда/Действие", "💌 Сигнал"],
    ],
    "analytics": [
        ["⭐ Карточка пары", "📊 Настроение"],
        ["🎉 Wrapped", "📄 Экспорт CSV"],
    ],
    "memories": [
        ["➕ Сохранить", "🎲 Случайное"],
        ["📖 Лента"],
    ],
    "games": [
        ["❓ Викторина", "🎲 Дуэль (КНБ)"],
        ["🎯 Совместные цели"],
    ],
    "achievements": [
        ["🏆 Достижения", "💰 Баланс очков"],
    ],
    "settings": [
        ["🎮 Модули", "🕐 Часовой пояс"],
        ["✏️ Имя пары", "🖼 Профиль"],
    ],
}


def build_module_menu(module: str) -> ReplyKeyboardMarkup:
    """Возвращает ReplyKeyboard для модуля с кнопкой «🏠 В меню» внизу."""
    rows = MODULE_BUTTONS.get(module, [])
    keyboard = [[KeyboardButton(text=btn) for btn in row] for row in rows]
    # Кнопка возврата — всегда последней строкой
    keyboard.append([KeyboardButton(text=HOME_BTN)])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )


# Обратный маппинг: «текст кнопки» -> (модуль, действие)
# Используется в menu.py для роутинга нажатий
BUTTON_ROUTES: dict[str, tuple[str, str]] = {
    # reminders
    "➕ Создать":           ("reminders", "create"),
    "📋 Список":            ("reminders", "list"),
    "🔁 Повторы":           ("reminders", "repeats"),
    "🗑 Удалить":           ("reminders", "delete"),
    # shopping
    "➕ Добавить":          ("shopping",  "add"),
    "✅ Куплено":           ("shopping",  "done"),
    # budget
    "➕ Трата":             ("budget",    "add"),
    "📊 Отчёт":            ("budget",    "report"),
    "💰 Лимит":            ("budget",    "limit"),
    "📈 График":           ("budget",    "chart"),
    # mood
    "😊 Отметить":         ("mood",      "ask"),
    "📅 История":          ("mood",      "history"),
    # dates
    "⏳ Обратный отсчёт":  ("dates",     "countdown"),
    "💌 Капсула":          ("dates",     "capsule"),
    # gratitude
    "💌 Сказать спасибо":  ("gratitude", "add"),
    "📜 Отчёт месяца":     ("gratitude", "report"),
    # romance
    "❓ Вопрос дня":       ("romance",   "question"),
    "🔥 Челлендж":         ("romance",   "challenge"),
    "🎲 Правда/Действие":  ("romance",   "td"),
    "💌 Сигнал":           ("romance",   "signal"),
    # analytics
    "⭐ Карточка пары":    ("analytics", "stats"),
    "📊 Настроение":       ("analytics", "mood"),
    "🎉 Wrapped":          ("analytics", "wrapped"),
    "📄 Экспорт CSV":      ("analytics", "csv"),
    # memories
    "➕ Сохранить":         ("memories",  "add"),
    "🎲 Случайное":         ("memories",  "random"),
    "📖 Лента":            ("memories",  "list"),
    # games
    "❓ Викторина":         ("games",     "quiz"),
    "🎲 Дуэль (КНБ)":      ("games",     "duel"),
    "🎯 Совместные цели":   ("games",     "goals"),
    # achievements
    "🏆 Достижения":        ("achievements", "list"),
    "💰 Баланс очков":      ("achievements", "balance"),
    # settings
    "🎮 Модули":            ("settings",  "modules"),
    "🕐 Часовой пояс":      ("settings",  "tz"),
    "✏️ Имя пары":          ("settings",  "name"),
    "🖼 Профиль":           ("settings",  "profile"),
}
