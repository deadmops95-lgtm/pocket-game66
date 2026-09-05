import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import time
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS

TOKEN = "8991300297:AAGP__SbLKFoPL-EZvsNvt85U1hilx3rqdg"

bot = Bot(token=TOKEN)
dp = Dispatcher()

app = Flask(__name__)
CORS(app)  # Разрешаем запросы от нашей игры

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

# --- API СЕРВЕРА ---
@app.route("/api/get_user/<int:user_id>", methods=["GET"])
def api_get_user(user_id):
    return jsonify(get_player_data(user_id))

@app.route("/api/save_user/<int:user_id>", methods=["POST"])
def api_save_user(user_id):
    data = request.json
    save_player_data(user_id, data)
    return jsonify({"status": "success"})

# --- ТЕЛЕГРАМ БОТ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    get_player_data(user_id)
    
    # Сюда позже пропишешь ссылку на свой GitHub Pages с игрой
    web_app_url = "https://твой-логин.github.io/репозиторий/"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть в Покемонов", web_app=WebAppInfo(url=web_app_url))]
    ])
    
    await message.answer(
        "👋 Добро пожаловать в мир покемонов!\n"
        "Жми кнопку ниже, чтобы запустить игру:",
        reply_markup=keyboard
    )

def run_flask():
    # Render передает порт через переменные окружения, либо используем 8000
    app.run(host="0.0.0.0", port=8000)

async def main():
    init_db()
    # Запуск Flask в фоне
    threading.Thread(target=run_flask, daemon=True).start()
    print("Бот и Flask-сервер запущены!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
