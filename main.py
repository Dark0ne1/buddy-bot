import asyncio
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from aiogram import Bot, Dispatcher, types
from aiogram.types import BotCommand, BotCommandScopeDefault
from config import TOKEN
from database import init_db
from handlers import common, venting, rational, wins, admin, mock_screens
from services.scheduler import setup_scheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

# Функция для настройки кнопки Меню
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Перезапуск бота"), # Neutral text
        BotCommand(command="help", description="Инструкция по использованию"), # Neutral text
        BotCommand(command="wins", description="Управление сохраненными данными"), # Neutral text
        BotCommand(command="hard_reset", description="Сброс настроек пользователя") # Neutral text
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

async def main():
    # 1. Инициализация БД
    await init_db()
    
    # 2. Бот и Диспетчер
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # 3. Подключение роутеров (ПОРЯДОК ВАЖЕН!)
    dp.include_router(admin.router)     # Адмика
    dp.include_router(mock_screens.router)
    dp.include_router(common.router)    # /start, регистрация
    dp.include_router(venting.router)   # Режим "Вентилятор"
    dp.include_router(rational.router)  # Режим "Рационализатор"
    dp.include_router(wins.router)      # Победы и ловушка (в конце)
    
    # 4. Настройка шедулера
    scheduler = setup_scheduler(bot)
    scheduler.start()
    
    # 5. Установка команд в меню
    await set_commands(bot)
    
    print("✅ AIogram Bot Template запущен! Нажми Ctrl+C для остановки.") # Neutral branding
    
    try:
        # Запуск поллинга
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске: {e}")
    finally:
        # Корректное завершение
        print("🛑 Остановка бота...")
        await bot.session.close()
        scheduler.shutdown()
        print("👋 Бот остановлен.")

if __name__ == "__main__":
    # Фикс для Windows (Event Loop)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Этот блок ловит Ctrl+C до того, как asyncio выдаст ошибку
        pass
