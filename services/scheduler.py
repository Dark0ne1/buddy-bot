import logging
from aiogram import Bot
import aiosqlite
from config import DB_NAME
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from database import get_all_users_ids, has_wins_today, reset_daily_usage # <-- Добавил reset_daily_usage
from config import TZ_MOSCOW, main_kb
from services.ai_service import generate_weekly_analysis

async def daily_evening_check(bot):
    print(f"🔍 [{datetime.now()}] Проверяю активность...")
    users = await get_all_users_ids()
    for (user_id,) in users:
        if await has_wins_today(user_id): continue
        try:
            await bot.send_message(
                user_id,
                "🌚 21:00. Тишина в эфире...\nЗапиши хоть одну мелочь. 👇",
                reply_markup=main_kb
            )
        except Exception: pass

async def send_weekly_summary(bot: Bot):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            users = await cursor.fetchall()

        for (user_id,) in users:
            async with db.execute("""
                SELECT created_at, text FROM wins 
                WHERE user_id = ? AND created_at >= date('now', '-7 days')
                ORDER BY created_at DESC
            """, (user_id,)) as cursor:
                wins = await cursor.fetchall()

            if wins:
                wins_text_list = [w[1] for w in wins]
                ai_praise = await generate_weekly_analysis(wins_text_list, user_name="Чемпион")

                text = f"📅 **Итоги твоей недели**\n\n"
                text += f"_{ai_praise}_\n\n"
                text += "**Твои факты:**\n"
                
                for date_str, win in wins:
                    text += f"✅ {win}\n"
                
                text += "\n🚀 Следующая неделя будет ещё круче!"

                try:
                    await bot.send_message(user_id, text, parse_mode="Markdown")
                except Exception as e:
                    logging.error(f"Не смог отправить отчет юзеру {user_id}: {e}")

def setup_scheduler(bot):
    scheduler = AsyncIOScheduler()
    
    # 1. Ежедневная напоминалка в 21:00
    scheduler.add_job(daily_evening_check, 'cron', hour=21, minute=0, timezone=TZ_MOSCOW, args=[bot])
    
    # 2. Еженедельный отчет в Воскресенье 20:00
    scheduler.add_job(send_weekly_summary, 'cron', day_of_week='sun', hour=20, minute=0, timezone=TZ_MOSCOW, args=[bot])
    
    # 3. Сброс лимитов AI в 00:00 (НОВОЕ)
    scheduler.add_job(reset_daily_usage, 'cron', hour=0, minute=0, timezone=TZ_MOSCOW)
    
    return scheduler
