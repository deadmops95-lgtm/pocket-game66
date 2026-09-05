import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import time
import threading
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

TOKEN = "8991300297:AAGP__SbLKFoPL-EZvsNvt85U1hilx3rqdg"

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
            is_evolved INTEGER DEFAULT 0
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
        }
    }

def save_player_data(user_id, data):
    conn = sqlite3.connect("game.db", check_same_thread=False)
    cursor = conn.cursor()
    poke = data["pokemon"]
    cursor.execute("""
        UPDATE players SET 
            energy = ?, max_energy = ?, candies = ?, rating = ?, wins = ?, loses = ?, last_login = ?,
            name = ?, type = ?, sprite_id = ?, level = ?, exp = ?, max_exp = ?,
            hp = ?, max_hp = ?, atk = ?, is_evolved = ?
        WHERE user_id = ?
    """, (
        data["energy"], data["maxEnergy"], data["candies"], data["rating"], data["wins"], data["loses"], data["lastLogin"],
        poke["name"], poke["type"], poke["spriteId"], poke["level"], poke["exp"], poke["maxExp"],
        poke["hp"], poke["maxHp"], poke["atk"], int(poke["isEvolved"]),
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

# --- ТЕЛЕГРАМ БОТ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    get_player_data(user_id)
    
    # Ссылка на твой GitHub Pages успешно прописана:
    web_app_url = "https://deadmops95-lgtm.github.io/pocket-game66/"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть в Покемонов", web_app=WebAppInfo(url=web_app_url))]
    ])
    
    await message.answer(
        "👋 Добро пожаловать в мир покемонов!\n"
        "Жми кнопку ниже, чтобы запустить игру:",
        reply_markup=keyboard
    )

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def main():
    init_db()
    threading.Thread(target=run_fastapi, daemon=True).start()
    print("Бот и FastAPI сервер запущены!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
