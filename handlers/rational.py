from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
import aiosqlite

from config import BTN_BACK, main_kb, cancel_kb, DB_NAME, BTN_ACTION_4 # BTN_ACTION_4 соответствует "Разобрать страх"
from handlers.common import BotStates
from database import get_user_role, get_rational_usage, increment_rational_usage # <-- Новые импорты
from services.ai_service import generate_rational_response, check_crisis_keywords, CRISIS_MESSAGE

router = Router()

# 1. Сначала хендлер КНОПКИ (вход в режим)
@router.message(F.text == BTN_ACTION_4)
async def start_rational(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.rational_mode)
    await state.update_data(history=[])
    await message.answer("Введите текст для анализа.", reply_markup=cancel_kb) # TODO: Customize text

# 2. Хендлер ВЫХОДА (В меню)
@router.message(BotStates.rational_mode, F.text.contains("В меню"))
async def stop_rational(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Режим анализа завершен. Возврат в главное меню.", reply_markup=main_kb) # TODO: Customize text

# 3. ОСНОВНОЙ ХЕНДЛЕР (Обработка текста)
@router.message(BotStates.rational_mode)
async def analyze_fear(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    # --- БЛОК БЕЗОПАСНОСТИ (Суицид) ---
    if check_crisis_keywords(message.text):
        await message.answer(
            CRISIS_MESSAGE, 
            parse_mode="HTML",
            reply_markup=main_kb
        )
        await state.clear()
        return
    # ----------------------------------

    # --- БЛОК МОНЕТИЗАЦИИ (Лимиты) ---
    usage, is_donator = await get_rational_usage(user_id)
    
    # Лимит: 10 запросов. Если не донатер и превысил - стоп.
    if not is_donator and usage >= 3:
        await message.answer(
            "🛑 <b>Лимит использования исчерпан.</b>\n\n" # TODO: Customize text
            "Доступно {limit} запросов в сутки. Лимиты обновятся в 00:00.\n\n"
            "🚀 <b>Для снятия ограничений:</b>\n"
            "Нажмите /donate.", # TODO: Customize monetization text
            parse_mode="HTML",
            reply_markup=main_kb
        )
        await state.clear()
        return
        
    # Увеличиваем счетчик (если прошли проверку)
    await increment_rational_usage(user_id)
    # ---------------------------------

    user_name = message.from_user.first_name or "Пользователь" # Neutral fallback
    role = await get_user_role(user_id)
    
    # 1. Достаем историю
    data = await state.get_data()
    history = data.get("history", [])
    history.append({"role": "user", "content": message.text})
    if len(history) > 10: history = history[-10:]

    wait = await message.answer("Обработка запроса...") # Neutral text
    
    # 2. Достаем последние победы (RAG)
    wins_list = []
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT text FROM wins WHERE user_id = ? ORDER BY created_at DESC LIMIT 100", (user_id,)) as cursor:
                rows = await cursor.fetchall()
                wins_list = [row[0] for row in rows]
    except Exception as e:
        print(f"⚠️ DEBUG ERROR: Ошибка БД: {e}")

    # 3. Генерируем ответ
    response = await generate_rational_response(role, user_name, history, wins_list)
    
    await wait.delete()
    
    history.append({"role": "assistant", "content": response})
    await state.update_data(history=history)

    await message.answer(response, parse_mode="Markdown")
