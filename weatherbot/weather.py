import requests
import os
from geopy.geocoders import Nominatim

CWA_API_KEY = os.environ.get('CWA_API_KEY', '')
CWA_BASE_URL = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore'

# 縣市對應的預報 API locationName
COUNTY_MAP = {
    '臺北市': '臺北市', '台北市': '臺北市',
    '新北市': '新北市',
    '桃園市': '桃園市',
    '臺中市': '臺中市', '台中市': '臺中市',
    '臺南市': '臺南市', '台南市': '臺南市',
    '高雄市': '高雄市',
    '基隆市': '基隆市',
    '新竹市': '新竹市',
    '新竹縣': '新竹縣',
    '苗栗縣': '苗栗縣',
    '彰化縣': '彰化縣',
    '南投縣': '南投縣',
    '雲林縣': '雲林縣',
    '嘉義市': '嘉義市',
    '嘉義縣': '嘉義縣',
    '屏東縣': '屏東縣',
    '宜蘭縣': '宜蘭縣',
    '花蓮縣': '花蓮縣',
    '臺東縣': '臺東縣', '台東縣': '臺東縣',
    '澎湖縣': '澎湖縣',
    '金門縣': '金門縣',
    '連江縣': '連江縣',
}


def get_county_from_coords(lat: float, lon: float) -> str | None:
    """用 GPS 座標取得縣市名稱"""
    try:
        geolocator = Nominatim(user_agent="weatherbot_taiwan")
        location = geolocator.reverse(f"{lat}, {lon}", language='zh-TW', timeout=5)

        if not location:
            return None

        address = location.raw.get('address', {})

        # 依序嘗試取得縣市
        county = (
            address.get('city') or
            address.get('county') or
            address.get('state')
        )

        if not county:
            return None

        # 標準化縣市名稱
        for key in COUNTY_MAP:
            if key in county:
                return COUNTY_MAP[key]

        return county

    except Exception as e:
        print(f"[Geocoding Error] {e}")
        return None


def get_weather_forecast(county: str) -> dict | None:
    """從中央氣象署取得縣市天氣預報"""
    try:
        # F-C0032-001：一般天氣預報-今明36小時天氣預報
        url = f"{CWA_BASE_URL}/F-C0032-001"
        params = {
            'Authorization': CWA_API_KEY,
            'locationName': county,
            'elementName': 'Wx,PoP,MinT,MaxT,CI'  # 天氣現象、降雨機率、最低/高溫、舒適度
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        locations = data['records']['location']
        if not locations:
            return None

        location = locations[0]
        elements = {el['elementName']: el['time'] for el in location['weatherElement']}

        # 取最近一筆資料
        weather = {
            'county': county,
            'description': elements['Wx'][0]['parameter']['parameterName'],
            'rain_prob': elements['PoP'][0]['parameter']['parameterName'],
            'temp_min': elements['MinT'][0]['parameter']['parameterName'],
            'temp_max': elements['MaxT'][0]['parameter']['parameterName'],
            'comfort': elements['CI'][0]['parameter']['parameterName'],
        }
        return weather

    except Exception as e:
        print(f"[Weather API Error] {e}")
        return None


def get_weather_by_location(lat: float, lon: float) -> dict | None:
    """主要入口：用座標取得完整天氣資訊"""
    county = get_county_from_coords(lat, lon)
    if not county:
        print(f"[Warning] 無法解析縣市：{lat}, {lon}")
        return None

    weather = get_weather_forecast(county)
    if weather:
        weather['lat'] = lat
        weather['lon'] = lon

    return weather


def has_significant_change(old_weather: dict, new_weather: dict) -> tuple[bool, str]:
    """
    比較兩次天氣資料，判斷是否有重大變化
    回傳 (是否有變化, 變化描述)
    """
    reasons = []

    try:
        old_rain = int(old_weather.get('rain_prob', 0))
        new_rain = int(new_weather.get('rain_prob', 0))

        # 降雨機率超過 60% 且上次低於 40%
        if new_rain >= 60 and old_rain < 40:
            reasons.append(f"降雨機率上升至 {new_rain}%，記得帶傘！")

        # 降雨機率從高到低（雨停了）
        if old_rain >= 60 and new_rain < 30:
            reasons.append(f"降雨機率下降至 {new_rain}%，天氣好轉！")

    except (ValueError, TypeError):
        pass

    try:
        old_min = int(old_weather.get('temp_min', 20))
        old_max = int(old_weather.get('temp_max', 30))
        new_min = int(new_weather.get('temp_min', 20))
        new_max = int(new_weather.get('temp_max', 30))

        old_avg = (old_min + old_max) / 2
        new_avg = (new_min + new_max) / 2

        # 溫度變化超過 5°C
        if abs(new_avg - old_avg) >= 5:
            if new_avg < old_avg:
                reasons.append(f"氣溫驟降，注意保暖！（{new_min}°C ~ {new_max}°C）")
            else:
                reasons.append(f"氣溫上升，注意防曬！（{new_min}°C ~ {new_max}°C）")

    except (ValueError, TypeError):
        pass

    # 天氣現象改變
    old_desc = old_weather.get('description', '')
    new_desc = new_weather.get('description', '')
    if old_desc != new_desc and new_desc:
        reasons.append(f"天氣由「{old_desc}」轉變為「{new_desc}」")

    has_change = len(reasons) > 0
    message = '\n'.join(f"• {r}" for r in reasons)

    return has_change, message
