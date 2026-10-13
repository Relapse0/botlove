"""Генерация PNG-карточек-заголовков для каждого модуля.

Карточка: 1200x400, градиентный фон, большая эмодзи-иконка, название.
Результат кешируется в /tmp/cards/ — повторный вызов возвращает готовый файл.
"""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# --- Конфигурация модулей -------------------------------------------
MODULE_META: dict[str, dict] = {
    "reminders":    {"icon": "🔔", "title": "Напоминания",  "colors": ("#1a1a2e", "#16213e", "#0f3460")},
    "shopping":     {"icon": "🛒", "title": "Покупки",      "colors": ("#1a2a1a", "#1e3a1e", "#2d5a27")},
    "budget":       {"icon": "💰", "title": "Бюджет",       "colors": ("#1a1500", "#2a2000", "#4a3800")},
    "mood":         {"icon": "😊", "title": "Настроение",   "colors": ("#1a0a2e", "#2d1b4e", "#4a2d7a")},
    "dates":        {"icon": "📅", "title": "Даты",         "colors": ("#1a0a0a", "#2e1515", "#4a2020")},
    "gratitude":    {"icon": "💌", "title": "Спасибо",      "colors": ("#1a0a15", "#2e1525", "#4a2040")},
    "romance":      {"icon": "🔥", "title": "Романтика",    "colors": ("#1a0500", "#2e0f00", "#4a1a00")},
    "analytics":    {"icon": "📊", "title": "Статистика",   "colors": ("#001a2e", "#002e4a", "#004a70")},
    "memories":     {"icon": "🖼",  "title": "Воспоминания", "colors": ("#0a1a1a", "#152e2e", "#1f4a4a")},
    "games":        {"icon": "🎮", "title": "Игры",         "colors": ("#100a1a", "#1e152e", "#2d1f4a")},
    "achievements": {"icon": "🏆", "title": "Уровни",       "colors": ("#1a1000", "#2e1f00", "#4a3200")},
    "settings":     {"icon": "⚙️", "title": "Настройки",    "colors": ("#0f0f0f", "#1a1a1a", "#2a2a2a")},
}

CARD_W, CARD_H = 1200, 400
CACHE_DIR = Path("/tmp/cards")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Шрифты: используем стандартный Linux-шрифт, если нет кастомного
_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]
_EMOJI_FONT_PATHS = [
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/noto/NotoColorEmoji.ttf",
]


def _load_font(size: int, paths: list[str]) -> ImageFont.FreeTypeFont:
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _gradient_bg(colors: tuple[str, str, str]) -> Image.Image:
    """Рисует горизонтальный градиент из трёх цветов."""
    img = Image.new("RGB", (CARD_W, CARD_H))
    draw = ImageDraw.Draw(img)

    def hex2rgb(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    c1, c2, c3 = hex2rgb(colors[0]), hex2rgb(colors[1]), hex2rgb(colors[2])
    half = CARD_W // 2
    for x in range(CARD_W):
        t = x / (CARD_W - 1)
        if t < 0.5:
            s = t * 2
            r = int(c1[0] + (c2[0] - c1[0]) * s)
            g = int(c1[1] + (c2[1] - c1[1]) * s)
            b = int(c1[2] + (c2[2] - c1[2]) * s)
        else:
            s = (t - 0.5) * 2
            r = int(c2[0] + (c3[0] - c2[0]) * s)
            g = int(c2[1] + (c3[1] - c2[1]) * s)
            b = int(c2[2] + (c3[2] - c2[2]) * s)
        draw.line([(x, 0), (x, CARD_H)], fill=(r, g, b))
    return img


def generate_card(module: str) -> Path:
    """Генерирует PNG-карточку для модуля. Возвращает путь к файлу."""
    out = CACHE_DIR / f"{module}.png"
    if out.exists():
        return out

    meta = MODULE_META.get(module, {
        "icon": "❓", "title": module, "colors": ("#1a1a1a", "#2a2a2a", "#3a3a3a")
    })

    img = _gradient_bg(meta["colors"])
    draw = ImageDraw.Draw(img)

    # Декоративная полоска слева
    for i in range(8):
        alpha = 180 - i * 20
        draw.rectangle([(30 + i * 3, 40), (30 + i * 3 + 2, CARD_H - 40)],
                       fill=(255, 255, 255, alpha))

    # Название модуля — большой текст справа от иконки
    font_title = _load_font(96, _FONT_PATHS)
    font_sub   = _load_font(48, _FONT_PATHS)

    title = meta["title"]
    icon  = meta["icon"]

    # Центрируем название по вертикали
    title_w, title_h = draw.textlength(title, font=font_title), 96
    x_title = (CARD_W - title_w) / 2
    y_title = (CARD_H - title_h) / 2 - 20

    # Тень для читаемости
    draw.text((x_title + 3, y_title + 3), title, font=font_title, fill=(0, 0, 0, 120))
    draw.text((x_title, y_title), title, font=font_title, fill=(255, 255, 255))

    # Подпись "couple bot" внизу
    sub = "couple bot"
    sub_w = draw.textlength(sub, font=font_sub)
    draw.text(((CARD_W - sub_w) / 2, CARD_H - 80), sub,
              font=font_sub, fill=(255, 255, 255, 100))

    img.save(out, "PNG", optimize=True)
    return out


def bust_cache(module: str | None = None) -> None:
    """Сбросить кеш карточки(ок) при изменении стиля."""
    if module:
        p = CACHE_DIR / f"{module}.png"
        if p.exists():
            p.unlink()
    else:
        for p in CACHE_DIR.glob("*.png"):
            p.unlink()
