from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import LabeledPrice, PreCheckoutQuery

from database import get_user_role, upsert_user, add_win, set_donator
from config import main_kb, BTN_ACTION_1, BTN_ACTION_2, BTN_ACTION_3, BTN_ACTION_4

router = Router()

class BotStates(StatesGroup):
    waiting_for_role = State()
    waiting_for_first_win = State()
    venting_mode = State()
    venting_decision = State()
    rational_mode = State()

# ==========================================
# 1. КОМАНДЫ (Глобальные)
# ==========================================

@router.message(Command("help"), StateFilter("*"))
async def command_help(message: types.Message):
    text = (
        "🤖 <b>Инструкция:</b>\n\n" # TODO: Customize bot name
        f"1. <b>{BTN_ACTION_1}</b> — Описание действия 1.\n" # TODO: Customize text
        f"2. <b>{BTN_ACTION_2}</b> — Описание действия 2.\n" # TODO: Customize text
        f"3. <b>{BTN_ACTION_3}</b> — Описание действия 3.\n" # TODO: Customize text
        f"4. <b>{BTN_ACTION_4}</b> — Описание действия 4.\n\n" # TODO: Customize text
        "🔄 <b>/hard_reset</b> — Сброс настроек / Повторный онбординг.\n"
        "🆘 <b>/support</b> — Связаться с поддержкой.\n"
        "☕️ <b>/donate</b> — Снять лимиты и поддержать проект." # TODO: Customize monetization text
        "⚠️ <i>Дисклеймер: Бот предоставляет информацию. При необходимости обратитесь к специалисту.</i>" # TODO: Customize disclaimer
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("hard_reset"), StateFilter("*"))
async def hard_reset(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🔄 <b>Перезагрузка...</b>\n\n"
        "Начинаем настройку с чистого листа. (Данные пользователя сохранены).", # TODO: Customize text
        parse_mode="HTML"
    )
    await state.set_state(BotStates.waiting_for_role)
    await message.answer("Кто ты по профессии сейчас?")

# ==========================================
# 2. ОПЛАТА (DONATE)
# ==========================================


# ==========================================
# 3. START И ОНБОРДИНГ
# ==========================================

@router.message(CommandStart(), StateFilter("*"))
async def command_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    user_name = message.from_user.first_name
    current_role = await get_user_role(message.from_user.id)
    
    # Если роль есть — просто приветствуем
    if current_role and current_role != "Человек":
        await message.answer(
            f"👋 С возвращением, <b>{user_name}</b>!\n"
            f"Роль: <b>{current_role}</b>.\n\n"
            f"Выберите действие в меню.", # TODO: Customize welcome back message
            parse_mode="HTML",
            reply_markup=main_kb
        )
    # Если роли нет — запускаем ОНБОРДИНГ
    else:
        await state.set_state(BotStates.waiting_for_role)
        await message.answer(
            f"👋 <b>Привет, {user_name}! Я — AI-помощник.</b>\n\n" # TODO: Customize bot name
            "Это универсальный шаблон для работы с пользовательским вводом и AI-анализом.\n\n" # TODO: Customize intro text
            "Для начала настройки укажите: <b>Ваша основная роль/профессия?</b>\n"
            "<i>(Например: Разработчик, Менеджер, Студент)</i>", # TODO: Customize prompt
            parse_mode="HTML"
        )

# ШАГ 1: Получаем роль -> Просим победу
@router.message(BotStates.waiting_for_role)
async def set_role(message: types.Message, state: FSMContext):
    role = message.text.strip()
    if len(role) > 50:
        await message.answer("Ого, как длинно. Давай покороче (до 50 символов).")
        return
        
    await upsert_user(message.from_user.id, message.from_user.username, role)
    
    # Не пускаем в меню, а ведем на шаг 2
    await state.set_state(BotStates.waiting_for_first_win)
    
    await message.answer(
        f"Настройка завершена. Роль: <b>{role}</b>.\n\n" # TODO: Customize text
        "<b>Первый шаг:</b>\n"
        "Введите любой текст, который будет сохранен как ваш первый элемент данных.\n" # TODO: Customize text
        "Например: «Начал работу над проектом X»",
        parse_mode="HTML"
    )

# ШАГ 2: Получаем первую победу -> Пускаем в меню
@router.message(BotStates.waiting_for_first_win)
async def first_win(message: types.Message, state: FSMContext):
    win_text = message.text.strip()
    
    # Записываем в базу
    await add_win(message.from_user.id, win_text)
    
    await state.clear()
    
    await message.answer(
        "✅ <b>Данные сохранены!</b>\n\n"
        "Вы находитесь в главном меню.\n"
        f"<b>{BTN_ACTION_1}</b> — Описание действия 1.\n" # TODO: Customize text
        f"<b>{BTN_ACTION_4}</b> — Описание действия 4.\n" # TODO: Customize text
        f"<b>{BTN_ACTION_3}</b> — Описание действия 3.\n\n" # TODO: Customize text
        "Выберите действие.", # TODO: Customize text
        parse_mode="HTML",
        reply_markup=main_kb
    )

#=============================
# Поддержка
#=============================

@router.message(Command("support"), StateFilter("*"))
async def support_command(message: types.Message):
    text = (
        "🆘 <b>Поддержка и связь со мной:</b>\n\n"
        "Если что-то сломалось, есть идея или хочешь сотрудничать — пиши:\n\n"
        "• Контакт: [PLACEHOLDER_TELEGRAM_USERNAME]\n" # TODO: Replace with support contact
        "При обращении, пожалуйста, укажите:\n"
        "1) Что делал(а) в боте\n"
        "2) Что ожидал(а)\n"
        "3) Что получилось на самом деле.\n"
    )
    await message.answer(text, parse_mode="HTML")