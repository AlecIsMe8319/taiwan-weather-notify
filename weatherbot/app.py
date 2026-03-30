from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, LocationMessage, TextMessage, TextSendMessage
)
from .weather import get_weather_by_location
from .database import save_user_location, get_user_location
import os

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    """用戶傳送位置時觸發"""
    user_id = event.source.user_id
    lat = event.message.latitude
    lon = event.message.longitude

    # 取得天氣資訊
    weather_info = get_weather_by_location(lat, lon)

    if weather_info:
        # 儲存用戶位置到資料庫
        save_user_location(user_id, lat, lon, weather_info['county'])

        # 回傳天氣訊息
        message = format_weather_message(weather_info)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message)
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="⚠️ 無法取得天氣資訊，請稍後再試。")
        )


@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    """處理文字訊息"""
    text = event.message.text.strip()

    if text in ['天氣', '查天氣', 'weather']:
        reply = "📍 請傳送您的目前位置，我會幫您查詢當地天氣！\n\n點選下方「+」→「位置資訊」即可傳送。"
    elif text in ['說明', 'help', 'Help']:
        reply = (
            "🌤 WeatherBot 使用說明\n\n"
            "📍 傳送位置 → 查詢當地天氣\n"
            "🔔 自動通知 → 天氣有變化時會主動通知您\n"
            "🗺 縣市偵測 → 移動到不同縣市時自動推播天氣\n\n"
            "傳送「天氣」開始使用！"
        )
    else:
        reply = "請傳送您的位置查詢天氣 🌤\n或輸入「說明」查看使用方式。"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


def format_weather_message(weather_info: dict) -> str:
    """格式化天氣訊息"""
    county = weather_info.get('county', '未知')
    description = weather_info.get('description', '資料不足')
    temp_min = weather_info.get('temp_min', '-')
    temp_max = weather_info.get('temp_max', '-')
    rain_prob = weather_info.get('rain_prob', '-')
    wind = weather_info.get('wind', '-')

    # 天氣 emoji
    emoji = get_weather_emoji(description, rain_prob)

    message = (
        f"{emoji} {county} 天氣預報\n"
        f"{'─' * 20}\n"
        f"🌡 氣溫：{temp_min}°C ~ {temp_max}°C\n"
        f"🌧 降雨機率：{rain_prob}%\n"
        f"💨 風速：{wind}\n"
        f"📋 天氣：{description}\n"
        f"{'─' * 20}\n"
        f"⏰ 如天氣有重大變化，我會主動通知您！"
    )
    return message


def get_weather_emoji(description: str, rain_prob) -> str:
    """根據天氣描述回傳對應 emoji"""
    try:
        prob = int(rain_prob)
    except (ValueError, TypeError):
        prob = 0

    if prob >= 60:
        return '🌧'
    if '晴' in description:
        return '☀️'
    if '多雲' in description or '陰' in description:
        return '⛅'
    if '雨' in description:
        return '🌧'
    if '雷' in description:
        return '⛈'
    return '🌤'


if __name__ == "__main__":
    app.run(port=5000, debug=True)
