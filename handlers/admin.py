from aiogram import Router, types
from aiogram.filters import Command
import aiosqlite

from database import get_stats
from config import DB_NAME
from services.ai_service import generate_weekly_analysis

router = Router()

# ID администраторов
ADMIN_IDS = [] # TODO: Replace with actual admin Telegram IDs

@router.message(Command("admin"))
async def admin_stats(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return 

    stats = await get_stats()
    
    text = (
        "📊 <b>Статистика Бота:</b>\n\n" # TODO: Customize bot name
        f"👥 <b>Пользователей:</b> {stats['users']}\n"
        f"🏆 <b>Всего побед:</b> {stats['wins']}\n"
        f"🔥 <b>DAU (писали сегодня):</b> {stats['dau']}\n"
        f"💰 <b>Донатеров:</b> {stats['donators']}\n"
        f"------------------\n"
        f"<i>Средне побед на юзера: {round(stats['wins'] / stats['users'], 1) if stats['users'] > 0 else 0}</i>"
    )
    
    await message.answer(text, parse_mode="HTML")


@router.message(Command("test_summary"))
async def test_summary_command(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return 

    await message.answer("⏳ Генерирую тестовый отчет...")

    user_id = message.from_user.id
    
    async with aiosqlite.connect(DB_NAME) as db:
        # Берем последние 20 побед
        async with db.execute("""
            SELECT created_at, text FROM wins 
            WHERE user_id = ? 
            ORDER BY created_at DESC LIMIT 20
        """, (user_id,)) as cursor:
            wins = await cursor.fetchall()

    if not wins:
        await message.answer("Нет данных для анализа.")
        return

    wins_text_list = [w[1] for w in wins]
    user_name = message.from_user.first_name or "Пользователь" # Neutral fallback
    
    # 1. Сначала генерируем текст
    ai_analysis = await generate_weekly_analysis(wins_text_list, user_name) # Renamed variable for neutrality

    # 2. Потом чистим форматирование для Telegram
    # Заменяем двойные звезды (от Gemini) на одинарные (для Telegram Markdown)
    ai_analysis = ai_analysis.replace("**", "*")

    # Формируем текст
    text = f"📅 *Результат обработки запроса (Тест)*\n\n" # Neutral text
    text += f"_{ai_analysis}_\n\n"
    text += "*Обработанные данные:*\n" # Neutral text
    
    for date_str, win in wins[:7]:
        text += f"✅ {win}\n"
    
    text += "\n--- Конец отчета ---" # Neutral closing

    try:
        await message.answer(text, parse_mode="Markdown")
    except Exception:
        # Если вдруг разметка сломалась (бывает), отправляем без неё
        await message.answer(text)
