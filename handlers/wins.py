from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import random
from utils import split_text

from config import BTN_ACTION_1, BTN_ACTION_2, main_kb, BUTTON_TEXTS # BTN_ACTION_1 и BTN_ACTION_2
from database import add_win, get_wins_last_week, get_wins_with_ids, delete_win
from handlers.common import BotStates

router = Router()

@router.message(F.text == BTN_ACTION_1)
async def ask_win(message: types.Message):
    await message.answer("Введите данные для сохранения.") # TODO: Customize text

@router.message(F.text == BTN_ACTION_2)
async def manual_report(message: types.Message):
    wins = await get_wins_last_week(message.from_user.id)
    if not wins:
        await message.answer("Нет сохраненных данных за последнюю неделю.", reply_markup=main_kb) # TODO: Customize text
        return
        
    text = "<b>📅 Отчет за последнюю неделю:</b>\n\n" # TODO: Customize text
    for date_str, win in wins:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            date_fmt = dt.strftime('%d.%m')
        except:
            date_fmt = "??.??" # На случай ошибок парсинга даты
            
        text += f"🔹 <i>{date_fmt}</i> — {win}\n"
    
    # Отправляем частями, чтобы не упасть
    for chunk in split_text(text):
        await message.answer(chunk, parse_mode="HTML", reply_markup=main_kb)

# --- УПРАВЛЕНИЕ ПОБЕДАМИ (РЕДАКТИРОВАНИЕ) ---

@router.message(Command("wins", "mywins"))
async def show_my_wins(message: types.Message):
    # Показываем последние 10 побед для редактирования
    wins = await get_wins_with_ids(message.from_user.id, limit=10)
    
    if not wins:
        await message.answer("Список пуст.")
        return

    await message.answer("<b>📜 Последние 10 сохраненных элементов (жми ❌ чтобы удалить):</b>", parse_mode="HTML") # TODO: Customize text

    for win_id, text, created_at in wins:
        # Обрезаем длинный текст для превью (до 50 символов)
        short_text = (text[:50] + '...') if len(text) > 50 else text
        
        # Инлайн кнопка удаления с ID победы
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Удалить", callback_data=f"del_win_{win_id}")]
        ])
        
        await message.answer(f"🔹 {short_text}", reply_markup=kb)

@router.callback_query(F.data.startswith("del_win_"))
async def delete_win_callback(callback: types.CallbackQuery):
    try:
        win_id = int(callback.data.split("_")[2])
        await delete_win(win_id)
        
        # Удаляем сообщение с победой из чата
        await callback.message.delete()
        await callback.answer("Удалено!", show_alert=False)
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)

# --- CATCH-ALL (Ловушка) ---
@router.message(lambda msg: msg.text and not msg.text.startswith("/"))
async def catch_win_text(message: types.Message, state: FSMContext):
    if await state.get_state() is not None: return
    if message.text in BUTTON_TEXTS: return
    if "Выпустить пар" in message.text or "Разобрать страх" in message.text: return

    await add_win(message.from_user.id, message.text)
    # Удаляем эмоциональные похвалы, заменяем на нейтральный ответ
    await message.answer("✅ Данные сохранены.", reply_markup=main_kb) # TODO: Customize confirmation text
