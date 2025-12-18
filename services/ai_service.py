from openai import AsyncOpenAI
from config import OPENAI_KEY, BOTHUB_BASE_URL, MODEL_NAME
import logging

client = AsyncOpenAI(api_key=OPENAI_KEY, base_url=BOTHUB_BASE_URL)

# --- SAFETY BLOCK ---
CRISIS_KEYWORDS = [
    "убить себя", "суицид", "не хочу жить", "вскрыть вены", "спрыгнуть", 
    "покончить с собой", "нет смысла жить", "хочу умереть", "выйти в окно",
    "вскрыться", "роскомнадзор", "выпилиться", "повеситься"
]

CRISIS_MESSAGE = (
    "Обнаружен потенциально опасный запрос. "
    "Обратитесь к специалисту или используйте другие ресурсы поддержки. "
    "Бот не предназначен для обработки кризисных ситуаций."
) # TODO: Customize crisis message and add relevant contact information if necessary

def check_crisis_keywords(text: str) -> bool:
    if not text: return False
    text = text.lower()
    for keyword in CRISIS_KEYWORDS:
        if keyword in text:
            return True
    return False

# --- PROMPTS ---

RATIONAL_SYSTEM_PROMPT = "SYSTEM PROMPT PLACEHOLDER FOR RATIONAL LOGIC. The user's role is {user_role} and name is {user_name}. Wins list is available if provided." # TODO: Replace with your own prompt for rationalization/analysis logic.

VENTING_SYSTEM_PROMPT = "SYSTEM PROMPT PLACEHOLDER FOR VENTING SUMMARY. The user's name is {user_name}." # TODO: Replace with your own prompt for summarizing user input.

WEEKLY_SUMMARY_SYSTEM_PROMPT = "SYSTEM PROMPT PLACEHOLDER FOR WEEKLY SUMMARY. The user's name is {user_name}." # TODO: Replace with your own prompt for generating weekly reports/summaries.

def get_rational_prompt(user_role, user_name):
    return RATIONAL_SYSTEM_PROMPT.format(user_role=user_role, user_name=user_name)

def get_venting_summary_prompt(user_name):
    return VENTING_SYSTEM_PROMPT.format(user_name=user_name)

def get_weekly_summary_prompt(user_name):
    return WEEKLY_SUMMARY_SYSTEM_PROMPT.format(user_name=user_name)

# --- FUNCTIONS ---

async def generate_rational_response(user_role, user_name, history, wins_list=None):
    try:
        system_content = get_rational_prompt(user_role, user_name)
        
        if wins_list:
            wins_str = "\n".join([f"- {w}" for w in wins_list])
            system_content += f"""
            
            ДОСЬЕ ПОБЕД ПОЛЬЗОВАТЕЛЯ:
            (Используй эти факты как доказательство его компетентности. Если уместно, ссылайся на них)
            {wins_str}
            """

        messages = [{"role": "system", "content": system_content}]
        messages.extend(history)

        completion = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"AI Error: {e}")
        return "Ошибка обработки запроса. Попробуйте позже." # TODO: Customize error message

async def generate_venting_summary(user_text_full, user_name="Друг"):
    try:
        completion = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": get_venting_summary_prompt(user_name)},
                {"role": "user", "content": f"Вот что я высказал:\n{user_text_full}"}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"AI Error: {e}")
        return "Ошибка обработки запроса. Попробуйте позже." # TODO: Customize error message

async def generate_weekly_analysis(wins_list, user_name="Друг"):
    if not wins_list:
        return "Нет данных для анализа." # TODO: Customize fallback message

    wins_text = "\n".join([f"- {w}" for w in wins_list])
    
    try:
        completion = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": get_weekly_summary_prompt(user_name)},
                {"role": "user", "content": f"Вот мои победы за неделю:\n{wins_text}"}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"AI Error (Summary): {e}")
        return "Ошибка обработки запроса. Попробуйте позже." # TODO: Customize error message
