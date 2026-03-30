from apscheduler.schedulers.background import BackgroundScheduler
from linebot import LineBotApi
from linebot.models import TextSendMessage
from .weather import get_weather_forecast, has_significant_change
from .database import get_all_users, update_user_weather, save_user_location
import os

line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])


def check_weather_changes():
    """
    排程任務：每 30 分鐘執行
    檢查所有用戶的天氣是否有重大變化，有的話主動推播
    """
    print("[Scheduler] 開始檢查天氣變化...")
    users = get_all_users()

    for user in users:
        user_id = user['user_id']
        county = user.get('county')
        old_weather = user.get('weather')

        if not county:
            continue

        # 取得最新天氣
        new_weather = get_weather_forecast(county)
        if not new_weather:
            continue

        # 如果是第一次或縣市一樣，檢查天氣變化
        if old_weather:
            has_change, change_desc = has_significant_change(old_weather, new_weather)

            if has_change:
                message = (
                    f"⚠️ {county} 天氣變化通知\n"
                    f"{'─' * 20}\n"
                    f"{change_desc}\n"
                    f"{'─' * 20}\n"
                    f"🌡 現在氣溫：{new_weather['temp_min']}°C ~ {new_weather['temp_max']}°C\n"
                    f"🌧 降雨機率：{new_weather['rain_prob']}%"
                )

                try:
                    line_bot_api.push_message(user_id, TextSendMessage(text=message))
                    print(f"[Push] 已推播天氣變化通知給 {user_id}（{county}）")
                except Exception as e:
                    print(f"[Push Error] {user_id}: {e}")

        # 更新資料庫的天氣基準
        update_user_weather(user_id, new_weather)

    print(f"[Scheduler] 完成，共檢查 {len(users)} 位用戶")


def check_county_change(user_id: str, new_lat: float, new_lon: float,
                         new_county: str, old_county: str,
                         new_weather: dict):
    """
    用戶傳送新位置時呼叫
    如果縣市改變，推播新縣市天氣
    """
    if old_county and old_county != new_county:
        message = (
            f"📍 偵測到您已移動到 {new_county}！\n"
            f"{'─' * 20}\n"
            f"🌡 氣溫：{new_weather['temp_min']}°C ~ {new_weather['temp_max']}°C\n"
            f"🌧 降雨機率：{new_weather['rain_prob']}%\n"
            f"📋 天氣：{new_weather['description']}\n"
            f"{'─' * 20}\n"
            f"🔔 已更新為 {new_county} 的天氣監控"
        )

        try:
            line_bot_api.push_message(user_id, TextSendMessage(text=message))
            print(f"[Push] 縣市切換通知：{old_county} → {new_county}（{user_id}）")
        except Exception as e:
            print(f"[Push Error] {e}")


def start_scheduler():
    """啟動排程器"""
    scheduler = BackgroundScheduler(timezone='Asia/Taipei')

    # 每 30 分鐘檢查一次天氣
    scheduler.add_job(
        check_weather_changes,
        'interval',
        minutes=30,
        id='weather_check',
        replace_existing=True
    )

    scheduler.start()
    print("[Scheduler] 排程器已啟動，每 30 分鐘檢查天氣")
    return scheduler
