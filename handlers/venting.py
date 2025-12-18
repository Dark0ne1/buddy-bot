import asyncio
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import random

from config import BTN_BACK, main_kb, cancel_kb, BTN_ACTION_3 # BTN_ACTION_3 соответствует "Выпустить пар"
from handlers.common import BotStates
from services.ai_service import generate_venting_summary, check_crisis_keywords, CRISIS_MESSAGE

router = Router()

burn_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Удалить диалог"), KeyboardButton(text="Сохранить диалог")] # Neutral buttons
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

@router.message(F.text == BTN_ACTION_3)
async def start_venting(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.venting_mode)
    # Инициализируем список для ID сообщений (чтобы потом удалить)
    # Добавляем ID самого первого сообщения пользователя (нажатие кнопки)
    await state.update_data(vent_messages=[], msg_ids=[message.message_id])
    
    msg = await message.answer("Режим ввода данных активирован. Введите информацию.", reply_markup=cancel_kb) # TODO: Customize text
    # Запоминаем ID ответа бота
    await _save_msg_id(state, msg.message_id)


# Вспомогательная функция для сохранения ID
async def _save_msg_id(state: FSMContext, msg_id: int):
    data = await state.get_data()
    ids = data.get("msg_ids", [])
    ids.append(msg_id)
    await state.update_data(msg_ids=ids)


# ШАГ 1: Юзер нажал "В меню" -> Генерируем поддержку
@router.message(BotStates.venting_mode, F.text.contains("В меню"))
async def stop_venting_step1(message: types.Message, state: FSMContext):
    # Сохраняем ID сообщения "В меню" тоже
    await _save_msg_id(state, message.message_id)
    
    data = await state.get_data()
    vent_msgs = data.get("vent_messages", [])
    user_name = message.from_user.first_name or "Друг"

    if not vent_msgs:
        await state.clear()
        await message.answer("Нет данных для обработки. Возврат в меню.", reply_markup=main_kb) # TODO: Customize text
        return

    wait = await message.answer("Обработка данных...") # Neutral text
    
    user_text_full = "\n".join(vent_msgs)
    if len(user_text_full) > 3000: user_text_full = user_text_full[-3000:]
    
    response = await generate_venting_summary(user_text_full, user_name)
    await wait.delete()
    
    # Отправляем поддержку
    summary_msg = await message.answer(response, parse_mode="Markdown")
    
    # Сохраняем ID саммари (чтобы при удалении оставить ТОЛЬКО его или удалить всё, по желанию)
    # Давай оставим саммари, а удалим только нытье.
    
    await state.set_state(BotStates.venting_decision)
    await message.answer(
        "Обработка завершена.\n\n" # Neutral text
        "Выберите действие с введенными сообщениями:\n"
        "<b>Удалить диалог</b> — сообщения будут удалены из чата.\n"
        "<b>Сохранить диалог</b> — сообщения останутся в чате.",
        parse_mode="HTML",
        reply_markup=burn_kb
    )

# ШАГ 2: Обработка выбора
@router.message(BotStates.venting_decision)
async def venting_decision(message: types.Message, state: FSMContext, bot: Bot):
    decision = message.text
    
    if "Удалить диалог" in decision:
        status_msg = await message.answer("Удаление сообщений...") # Neutral text
        
        data = await state.get_data()
        msg_ids = data.get("msg_ids", [])
        
        # Удаляем сообщения
        deleted_count = 0
        for mid in msg_ids:
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=mid)
                deleted_count += 1
                await asyncio.sleep(0.05) # Небольшая задержка, чтобы Телеграм не банил за флуд
            except Exception:
                pass # Если сообщение уже удалено или старое, игнорим
        
        await status_msg.edit_text(f"✅ Удалено {deleted_count} сообщений. Чат очищен.", parse_mode="HTML") # Neutral text
        # Через 3 секунды удаляем и сообщение о сжигании, чтобы было совсем чисто
        await asyncio.sleep(3)
        await status_msg.delete()
        
        await message.answer("Возврат в меню.", reply_markup=main_kb) # Neutral text
    else:
        await message.answer(
            "Сообщения сохранены.", # Neutral text
            reply_markup=main_kb
        )
    
    await state.clear()


# СЛУШАТЕЛЬ
@router.message(BotStates.venting_mode)
async def venting_listener(message: types.Message, state: FSMContext):
    # Сохраняем ID сообщения пользователя
    await _save_msg_id(state, message.message_id)

    if check_crisis_keywords(message.text):
        await message.answer(CRISIS_MESSAGE, parse_mode="HTML", reply_markup=main_kb)
        await state.clear()
        return

    data = await state.get_data()
    vent_msgs = data.get("vent_messages", [])
    vent_msgs.append(message.text)
    await state.update_data(vent_messages=vent_msgs)

    # Удаляем эмоциональные реакции, заменяем на нейтральный ответ
    reaction_msg = await message.answer("Данные приняты.") # Neutral reaction
    # Сохраняем ID реакции бота
    await _save_msg_id(state, reaction_msg.message_id)
