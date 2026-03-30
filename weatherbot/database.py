import sqlite3
import json
from datetime import datetime

DB_PATH = 'weatherbot.db'


def init_db():
    """初始化資料庫，建立資料表"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id     TEXT PRIMARY KEY,
                lat         REAL,
                lon         REAL,
                county      TEXT,
                weather     TEXT,       -- JSON 格式儲存天氣資料
                updated_at  TEXT
            )
        ''')
        conn.commit()
    print("[DB] 資料庫初始化完成")


def save_user_location(user_id: str, lat: float, lon: float,
                        county: str, weather: dict = None):
    """儲存或更新用戶位置"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            INSERT INTO users (user_id, lat, lon, county, weather, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                lat        = excluded.lat,
                lon        = excluded.lon,
                county     = excluded.county,
                weather    = excluded.weather,
                updated_at = excluded.updated_at
        ''', (
            user_id, lat, lon, county,
            json.dumps(weather, ensure_ascii=False) if weather else None,
            datetime.now().isoformat()
        ))
        conn.commit()


def get_user_location(user_id: str) -> dict | None:
    """取得用戶最後一次位置資料"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            'SELECT * FROM users WHERE user_id = ?', (user_id,)
        ).fetchone()

    if not row:
        return None

    result = dict(row)
    if result.get('weather'):
        result['weather'] = json.loads(result['weather'])

    return result


def get_all_users() -> list[dict]:
    """取得所有用戶（用於排程推播）"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT * FROM users').fetchall()

    users = []
    for row in rows:
        user = dict(row)
        if user.get('weather'):
            user['weather'] = json.loads(user['weather'])
        users.append(user)

    return users


def update_user_weather(user_id: str, weather: dict):
    """更新用戶儲存的天氣資料（推播後更新基準）"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            UPDATE users SET weather = ?, updated_at = ?
            WHERE user_id = ?
        ''', (
            json.dumps(weather, ensure_ascii=False),
            datetime.now().isoformat(),
            user_id
        ))
        conn.commit()


# 啟動時自動初始化
init_db()
