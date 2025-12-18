import aiosqlite
from datetime import datetime, timedelta
from config import DB_NAME

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS wins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                role TEXT
            )
        """)
        await db.commit()
    
    # Запускаем миграцию (добавляем новые колонки, если их нет)
    await check_and_create_columns()

# --- МИГРАЦИЯ (НОВОЕ) ---
async def check_and_create_columns():
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            # Пытаемся добавить колонку для лимитов
            await db.execute("ALTER TABLE users ADD COLUMN daily_rational_usage INTEGER DEFAULT 0")
        except: pass
        
        try:
            # Пытаемся добавить колонку для донатов
            await db.execute("ALTER TABLE users ADD COLUMN is_donator BOOLEAN DEFAULT 0")
        except: pass
        
        await db.commit()

async def upsert_user(user_id, username, role=None):
    async with aiosqlite.connect(DB_NAME) as db:
        if role:
            await db.execute("""
                INSERT INTO users (user_id, username, role) VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET role=excluded.role
            """, (user_id, username, role))
        else:
            await db.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?, NULL)", (user_id, username))
        await db.commit()

async def get_user_role(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT role FROM users WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else "Человек"

async def add_win(user_id, text):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO wins (user_id, text) VALUES (?, ?)", (user_id, text))
        await db.commit()

async def get_wins_last_week(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        async with db.execute(
            "SELECT created_at, text FROM wins WHERE user_id = ? AND created_at >= ? ORDER BY created_at DESC", 
            (user_id, seven_days_ago)
        ) as cursor:
            return await cursor.fetchall()

async def get_all_users_ids():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            return await cursor.fetchall()

async def has_wins_today(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        async with db.execute(
            "SELECT 1 FROM wins WHERE user_id = ? AND created_at >= ? LIMIT 1", 
            (user_id, today_start)
        ) as cursor:
            return await cursor.fetchone() is not None
            
async def delete_win(win_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM wins WHERE id = ?", (win_id,))
        await db.commit()

async def get_wins_with_ids(user_id, limit=10):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT id, text, created_at FROM wins WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", 
            (user_id, limit)
        ) as cursor:
            return await cursor.fetchall()

# --- ФУНКЦИИ ДЛЯ МОНЕТИЗАЦИИ (НОВЫЕ) ---

async def increment_rational_usage(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET daily_rational_usage = daily_rational_usage + 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_rational_usage(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT daily_rational_usage, is_donator FROM users WHERE user_id = ?", (user_id,)) as cursor:
            res = await cursor.fetchone()
            if not res: return (0, 0)
            return (res[0] if res[0] else 0, res[1] if res[1] else 0)

async def reset_daily_usage():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET daily_rational_usage = 0")
        await db.commit()

async def set_donator(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET is_donator = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        # Всего юзеров
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = (await cursor.fetchone())[0]
            
        # Всего побед
        async with db.execute("SELECT COUNT(*) FROM wins") as cursor:
            total_wins = (await cursor.fetchone())[0]
            
        # Донатеры
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_donator = 1") as cursor:
            donators = (await cursor.fetchone())[0]

        # Активные за сегодня (кто записал победу)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        async with db.execute("SELECT COUNT(DISTINCT user_id) FROM wins WHERE created_at >= ?", (today_start,)) as cursor:
            active_today = (await cursor.fetchone())[0]

        return {
            "users": total_users,
            "wins": total_wins,
            "donators": donators,
            "dau": active_today
        }