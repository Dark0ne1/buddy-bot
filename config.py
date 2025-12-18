import os
from dotenv import load_dotenv
from pytz import timezone
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

load_dotenv()

# --- KEYS ---
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# --- SETTINGS ---
BOTHUB_BASE_URL = os.getenv("AI_API_BASE_URL", 'https://api.openai.com/v1') # TODO: Replace with your AI API base URL if needed
MODEL_NAME = os.getenv("AI_MODEL_NAME", 'gpt-4o-mini') # TODO: Replace with your preferred model name
DB_NAME = "aiogram_ai_template.db"
TZ_MOSCOW = timezone('Europe/Moscow') # TODO: Customize timezone

# --- BUTTONS TEXT ---
BTN_ACTION_1 = "Action 1" # TODO: Customize text
BTN_ACTION_2 = "Action 2" # TODO: Customize text
BTN_ACTION_3 = "Action 3" # TODO: Customize text
BTN_ACTION_4 = "Action 4" # TODO: Customize text
BTN_BACK = "Back" # TODO: Customize text

# --- KEYBOARDS ---
main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text=BTN_ACTION_1), KeyboardButton(text=BTN_ACTION_2)],
    [KeyboardButton(text=BTN_ACTION_3), KeyboardButton(text=BTN_ACTION_4)]
], resize_keyboard=True)

cancel_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=BTN_BACK)]], resize_keyboard=True)

# --- CONSTANTS ---
BUTTON_TEXTS = [BTN_ACTION_1, BTN_ACTION_2, BTN_ACTION_3, BTN_ACTION_4, BTN_BACK, "/start"]
