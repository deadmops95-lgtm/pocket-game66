import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import time
import threading
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

TOKEN = "8991300297:AAGP__SbLKFoPL-EZvsNvt85U1hilx3rqdg"
ADMIN_IDS = [123456789] # Замени на свой Telegram ID, чтобы получить доступ к админке

bot = Bot(token=TOKEN)
dp = Dispatcher()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect("game.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            energy INTEGER DEFAULT 10,
            max_energy INTEGER DEFAULT 10,
            candies INTEGER DEFAULT 5,
            rating INTEGER DEFAULT 1200,
            wins INTEGER DEFAULT 0,
            loses INTEGER DEFAULT 0,
            last_login INTEGER DEFAULT 0,
            name TEXT DEFAULT 'Чармандер',
            type TEXT DEFAULT 'Огонь',
            sprite_id INTEGER DEFAULT 4,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            max_exp INTEGER DEFAULT 50,
            hp INTEGER DEFAULT 100,
            max_hp INTEGER DEFAULT 100,
            atk INTEGER DEFAULT 15,
            is_evolved INTEGER DEFAULT 0,
            streak_days INTEGER DEFAULT 1,
            last_streak_time INTEGER DEFAULT 0,
            location TEXT DEFAULT 'forest'
        )
    """)
    conn.commit()
    conn.close()

def get_player_data(user_id):
    conn = sqlite3.connect("game.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    current_time = int(time.time())
    
    if not row:
        cursor.execute("INSERT INTO players (user_id, last_login) VALUES (?, ?)", (user_id, current_time))
        conn.commit()
        cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
    conn.close()
    
    return {
        "energy": row[1],
        "maxEnergy": row[2],
        "candies": row[3],
        "rating": row[4],
        "wins": row[5],
        "loses": row[6],
        "lastLogin": row[7],
        "pokemon": {
            "name": row[8],
            "type": row[9],
            "spriteId": row[10],
            "level": row[11],
            "exp": row[12],
            "maxExp": row[13],
            "hp": row[14],
            "maxHp": row[15],
            "atk": row[16],
            "isEvolved": bool(row[17])
        },
        "streakDays": row[18],
        "lastStreakTime": row[19],
        "location": row[20]
    }

def save_player_data(user_id, data):
    conn = sqlite3.connect("game.db", check_same_thread=False)
    cursor = conn.cursor()
    poke = data["pokemon"]
    cursor.execute("""
        UPDATE players SET 
            energy = ?, max_energy = ?, candies = ?, rating = ?, wins = ?, loses = ?, last_login = ?,
            name = ?, type = ?, sprite_id = ?, level = ?, exp = ?, max_exp = ?,
            hp = ?, max_hp = ?, atk = ?, is_evolved = ?, streak_days = ?, last_streak_time = ?, location = ?
        WHERE user_id = ?
    """, (
        data["energy"], data["maxEnergy"], data["candies"], data["rating"], data["wins"], data["loses"], data["lastLogin"],
        poke["name"], poke["type"], poke["spriteId"], poke["level"], poke["exp"], poke["maxExp"],
        poke["hp"], poke["maxHp"], poke["atk"], int(poke["isEvolved"]),
        data.get("streakDays", 1), data.get("lastStreakTime", 0), data.get("location", "forest"),
        user_id
    ))
    conn.commit()
    conn.close()

# --- FASTAPI ЭНДПОИНТЫ ---
@app.get("/api/get_user/{user_id}")
def api_get_user(user_id: int):
    return get_player_data(user_id)

@app.post("/api/save_user/{user_id}")
async def api_save_user(user_id: int, request: Request):
    data = await request.json()
    save_player_data(user_id, data)
    return {"status": "success"}

# Админ-эндпоинт для проверки статистики
@app.get("/api/admin/stats/{admin_id}")
def api_admin_stats(admin_id: int):
    if admin_id not in ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Access denied")
    
    conn = sqlite3.connect("game.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM players")
    total_players = cursor.fetchone()[0]
    
    # Онлайн за последние 15 минут (900 секунд)
    current_time = int(time.time())
    cursor.execute("SELECT COUNT(*) FROM players WHERE ? - last_login < 900", (current_time,))
    online_players = cursor.fetchone()[0]
    conn.close()
    
    return {"totalPlayers": total_players, "onlinePlayers": online_players}

# Админ-эндпоинт для выдачи ресурсов игроку
@app.post("/api/admin/give/{admin_id}")
async def api_admin_give(admin_id: int, request: Request):
    if admin_id not in ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Access denied")
    
    body = await request.json()
    target_user_id = body.get("target_user_id")
    candies = body.get("candies", 0)
    
    conn = sqlite3.connect("game.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET candies = candies + ? WHERE user_id = ?", (candies, target_user_id))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Added {candies} candies to user {target_user_id}"}

# --- ТЕЛЕГРАМ БОТ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    get_player_data(user_id)
    
    web_app_url = "https://deadmops95-lgtm.github.io/pocket-game66/"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть в Покемонов", web_app=WebAppInfo(url=web_app_url))]
    ])
    
    # Если это админ, можно добавить кнопку админ-панели прямо в боте или открывать её внутри веб-приложения
    if user_id in ADMIN_IDS:
        keyboard.inline_keyboard.append([
            [InlineKeyboardButton(text="🛠 Админ-панель (Статистика)", callback_data="admin_stats")]
        ])

    await message.answer(
        "👋 Добро пожаловать в мир покемонов!\n"
        "Жми кнопку ниже, чтобы запустить игру:",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "admin_stats")
async def process_admin_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("У вас нет прав!", show_alert=True)
        return
    
    conn = sqlite3.connect("game.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM players")
    total = cursor.fetchone()[0]
    current_time = int(time.time())
    cursor.execute("SELECT COUNT(*) FROM players WHERE ? - last_login < 900", (current_time,))
    online = cursor.fetchone()[0]
    conn.close()
    
    await callback.message.answer(f"🛠 **Статистика сервера:**\n👤 Всего игроков: {total}\n🟢 Онлайн (15 мин): {online}")
    await callback.answer()

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def main():
    init_db()
    threading.Thread(target=run_fastapi, daemon=True).start()
    print("Бот и FastAPI сервер запущены!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
