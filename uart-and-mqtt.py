from machine import Pin 
from umqtt.simple import MQTTClient
import utime, xtools
import urequests, ujson
from machine import UART

xtools.connect_wifi_led() # 記得在 config.py 中設定 Wi-Fi 名稱與密碼
led = Pin(2, Pin.OUT)
led.value(0)

com = UART(2, 9600, tx=17, rx=16)
com.init(9600)
print('MicroPython Ready...') 

ADAFRUIT_IO_USERNAME = "" # 請填寫 Adafruit IO username
ADAFRUIT_IO_KEY      = "" # 請填寫 Adafruit IO key
FEED = "final-project.city"

API_key = "" # 請填寫 OpenWeatherMap API Key
CITIES_AND_COUNTRY_CODE = {
    "Sydney": "AU",           # UTC+10 雪梨, 澳洲
    "Tokyo": "JP",            # UTC+9 東京, 日本
    "Taipei": "TW",           # UTC+8 台北, 台灣
    "Beijing": "CN",          # UTC+8 北京, 中國
    "Moscow": "RU",           # UTC+3 莫斯科, 俄羅斯
    "Paris": "FR",            # UTC+2（夏令時間） 巴黎, 法國
    "London": "GB",           # UTC+1（夏令時間） 倫敦, 英國
    "New York": "US",         # UTC-4（夏令時間） 紐約, 美國
    "Mexico City": "MX",      # UTC-5（夏令時間） 墨西哥市, 墨西哥
    "Los Angeles": "US",      # UTC-7（夏令時間） 洛杉磯, 美國
}

CITY_ALIASES = {
    "SYD": "Sydney",
    "TYO": "Tokyo",
    "TPE": "Taipei",
    "BJS": "Beijing",
    "MOW": "Moscow",
    "PAR": "Paris",
    "LON": "London",
    "NYC": "New York",
    "MEX": "Mexico City",
    "LA":  "Los Angeles",
}

# MQTT 客戶端
client = MQTTClient (
    client_id = xtools.get_id(),
    server = "io.adafruit.com",
    user = ADAFRUIT_IO_USERNAME,
    password = ADAFRUIT_IO_KEY,
    ssl = False,
)

def sub_cb(topic, msg):
    decoded = msg.decode().strip()
    print("使用者輸入:", decoded)
    
    if decoded in CITIES_AND_COUNTRY_CODE:
        city = decoded
        alias = ""
        for k, v in CITY_ALIASES.items():
            if v == city:
                alias = k
                break

    elif decoded in CITY_ALIASES:
        city = CITY_ALIASES[decoded]
        alias = decoded
    else:
        print("無效的城市名稱或簡稱：", decoded)
        return
    
    msg_to_send = "loading\n"
    com.write(msg_to_send)
    print("已透過UART傳送loading訊號：", msg_to_send)
    
    city_info = get_and_update_info(city, CITIES_AND_COUNTRY_CODE[city])
    
    if city_info:
        temp = city_info["temp"]
        time = city_info["time"]
        utc = city_info["utc"]
        humidity = city_info["humidity"]
        weather = city_info["weather"]
        
        # 格式化並透過UART傳送
        msg_to_send = "CITY:{},ALIAS:{},TEMP:{:.2f},UTC:{},TIME:{},HUMIDITY:{},WEATHER:{}\n".format(city, alias, temp, utc, time, humidity, weather)
        com.write(msg_to_send)
        print("已透過UART傳送：", msg_to_send)
    

client.set_callback(sub_cb)   # 指定回撥函數來接收訊息
client.connect()              # 連線
    
topic = ADAFRUIT_IO_USERNAME + "/feeds/" + FEED
print(topic)
client.subscribe(topic)      # 訂閱主題

def get_info_for_city(city_name, country_code):
    url  = "https://api.openweathermap.org/data/2.5/weather?"
    url += "q=" + city_name.replace(" ", "%20") + "," + country_code #在 URL encoding 中，空格以"%20"或是"+"表示
    url += "&units=metric&lang=zh_tw&" # 單位：攝氏度，語言：繁體中文
    url += "appid=" + API_key
    
    try:
        response = urequests.get(url)
        if response.status_code == 200:
            data = ujson.loads(response.text)
            main_data = data.get("main", {})
            temp = main_data.get("temp")
            humidity = main_data.get("humidity")
            timezone = data.get("timezone")
            weather_data = data.get("weather", [])
            weather = weather_data[0].get("main")
            response.close() # 及時釋放資源
            if temp is not None and timezone is not None and humidity is not None and weather is not None:
                return {"temp" : temp, "timezone" : timezone, "humidity" : humidity, "weather" : weather}
            else:
                return None 
        else:
            response.close()
            return None
    except Exception as e:
        print("EXCEPTION:", repr(e))  
        return None
    
def get_and_update_info(city_name, country_code):
    current_info = get_info_for_city(city_name, country_code)
    current_temp = current_info["temp"]
    current_timezone = current_info["timezone"]
    current_humidity = current_info["humidity"]
    current_weather = current_info["weather"]
        
    if current_info is not None:
        # 計算該城市的當地時間（從 UTC 現在時間加 offset）
        utc_timestamp = utime.time() - 8 * 60 * 60
        local_timestamp = utc_timestamp + current_timezone
        local_timeuct = utime.localtime(local_timestamp)
        local_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            local_timeuct[0], local_timeuct[1], local_timeuct[2],
            local_timeuct[3], local_timeuct[4], local_timeuct[5]
        )
        utc = current_timezone / 60 / 60 # 紀錄 utc +- 幾

        # 組成 Feed Key
        adafruit_feed_key = city_name.replace(" ", "-")
        feed_group = "final-project"
        adafruit_url_base = f"https://io.adafruit.com/api/v2/{ADAFRUIT_IO_USERNAME}/feeds"

        # 傳送溫度
        temp_url = f"{adafruit_url_base}/{feed_group}.temp/data?X-AIO-Key={ADAFRUIT_IO_KEY}"
        print(f"{adafruit_feed_key} 當前溫度：{current_temp}°C")
        xtools.webhook_post(temp_url, {"value": current_temp})

        # 傳送時間
        time_url = f"{adafruit_url_base}/{feed_group}.time/data?X-AIO-Key={ADAFRUIT_IO_KEY}"
        print(f"{adafruit_feed_key} 當前時間：{local_time}")
        xtools.webhook_post(time_url, {"value": local_time})
        
        # 傳送濕度
        humidity_url = f"{adafruit_url_base}/{feed_group}.humidity/data?X-AIO-Key={ADAFRUIT_IO_KEY}"
        print(f"{adafruit_feed_key} 當前濕度：{current_humidity}")
        xtools.webhook_post(humidity_url, {"value": current_humidity})
        
        # 傳送天氣
        weather_url = f"{adafruit_url_base}/{feed_group}.weather/data?X-AIO-Key={ADAFRUIT_IO_KEY}"
        print(f"{adafruit_feed_key} 當前天氣：{current_weather}")
        xtools.webhook_post(weather_url, {"value": current_weather})
        
        return {"temp" : current_temp, "time" : local_time, "utc" : utc, "humidity" : current_humidity, "weather" : current_weather}
        
    else:
        print(f"未能獲取城市 {city_name} 的數據，本次跳過發送。")


while True:
    if com.any() > 0:
        response = com.readline().decode().strip()
        print("接收到: ", response)
        if response.startswith('Refresh,'):
            parts = response.strip().split(',')
            if len(parts) >= 3:
                city = parts[1]
                alias = parts[2]
                
                msg_to_send = "loading\n"
                com.write(msg_to_send)
                print("已透過UART傳送loading訊號：", msg_to_send)
                
                city_info = get_and_update_info(city, CITIES_AND_COUNTRY_CODE[city])
                if city_info:
                    temp = city_info["temp"]
                    time = city_info["time"]
                    utc = city_info["utc"]
                    humidity = city_info["humidity"]
                    weather = city_info["weather"]
                    
                    # 格式化並透過UART傳送
                    msg_to_send = "CITY:{},ALIAS:{},TEMP:{:.2f},UTC:{},TIME:{},HUMIDITY:{},WEATHER:{}\n".format(city, alias, temp, utc, time, humidity, weather)
                    com.write(msg_to_send)
                    print("已透過UART傳送：", msg_to_send)
            else:
                print("收到Refresh開頭但格式錯誤：", response)
    client.check_msg()
    utime.sleep(0.1)
    
    