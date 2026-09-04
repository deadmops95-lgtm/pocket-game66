import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import threading

# Твой токен бота
TOKEN = "8991300297:AAGP__SbLKFoPL-EZvsNvt85U1hilx3rqdg"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# FastAPI приложение для связи с игрой
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
            candies INTEGER DEFAULT 5,
            rating INTEGER DEFAULT 1200,
            wins INTEGER DEFAULT 0,
            loses INTEGER DEFAULT 0,
            name TEXT DEFAULT 'Флеймлинг',
            type TEXT DEFAULT 'Огонь',
            emoji TEXT DEFAULT '🔥',
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
    
    if not row:
        # Создаем игрока, если его нет
        cursor.execute("INSERT INTO players (user_id) VALUES (?)", (user_id,))
        conn.commit()
        cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
    conn.close()
    
    return {
        "energy": row[1],
        "candies": row[2],
        "rating": row[3],
        "wins": row[4],
        "loses": row[5],
        "pokemon": {
            "name": row[6],
            "type": row[7],
            "emoji": row[8],
            "level": row[9],
            "exp": row[10],
            "maxExp": row[11],
            "hp": row[12],
            "maxHp": row[13],
            "atk": row[14],
            "isEvolved": bool(row[15])
        }
    }

def save_player_data(user_id, data):
    conn = sqlite3.connect("game.db", check_same_thread=False)
    cursor = conn.cursor()
    poke = data["pokemon"]
    cursor.execute("""
        UPDATE players SET 
            energy = ?, candies = ?, rating = ?, wins = ?, loses = ?,
            name = ?, type = ?, emoji = ?, level = ?, exp = ?, max_exp = ?,
            hp = ?, max_hp = ?, atk = ?, is_evolved = ?
        WHERE user_id = ?
    """, (
        data["energy"], data["candies"], data["rating"], data["wins"], data["loses"],
        poke["name"], poke["type"], poke["emoji"], poke["level"], poke["exp"], poke["maxExp"],
        poke["hp"], poke["maxHp"], poke["atk"], int(poke["isEvolved"]),
        user_id
    ))
    conn.commit()
    conn.close()

# --- API ДЛЯ ИГРЫ ---
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
    get_player_data(user_id) # Инициализируем в БД
    
    # Ссылка на твое приложение (пока локальная для теста)
    web_app_url = "http://127.0.0.1:5500/index.html" # Или ссылка с GitHub Pages

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть в Nexomon", web_app=WebAppInfo(url=web_app_url))]
    ])
    
    await message.answer(
        "👋 С возвращением в мир Nexomon!\n"
        "Твой прогресс сохраняется на сервере. Нажми кнопку ниже, чтобы открыть игру:",
        reply_markup=keyboard
    )

def run_fastapi():
    uvicorn.run(app, host="127.0.0.1", port=8000)

async def main():
    init_db()
    # Запускаем FastAPI в отдельном потоке, чтобы бот и сервер работали одновременно
    threading.Thread(target=run_fastapi, daemon=True).start()
    print("Бот и сервер запущены!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
