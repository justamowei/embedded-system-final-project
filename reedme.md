# embedded-system-final-project 
嵌入式系統設計期末專案 — 01157032 何燿安

## 題目 
透過手機以 MQTT 輸入城市全名或縮寫，讓 ESP32 從 OpenWeatherMap 擷取該城市的時間、氣溫、濕度與天氣資訊，並將資料上傳至 Adafruit，同時傳送至連接 8051 的 oled 顯示器，還可以藉由 8051 按鍵切換顯示內容與刷新資訊。

## 介紹 
本 repo 中包含兩個主要檔案：`uart-and-mqtt.py` 與 `uart-and-oled.c`。

- `uart-and-mqtt.py` 需燒錄至 ESP32，負責：
  * 與手機進行 MQTT 通訊 
  * 從 OpenWeatherMap 取得指定城市的天氣資訊 
  * 將天氣資料上傳至 Adafruit 
  * 透過 UART 將資料傳送給 8051 

- `uart-and-oled.c` 需燒錄至 8051 開發板，負責：
  * 接收來自 ESP32 的 UART 資料 
  * 使用 I²C 將資料傳送至 OLED 顯示 
  * 回傳資料給 ESP32，以確認接收正確 
  * 發送「Refresh」指令給 ESP32 

## 使用範例 

### 前置準備 
- 接好 ESP32、8051 及 OLED（建議先燒錄 8051，再接上 ESP32 與 8051 間的 UART） 
- 手機安裝 IoT MQTT 工具 
- 設定好 Adafruit 與 OpenWeatherMap 所需的 API key，以及 Wi-Fi 帳號密碼 
- 在 Adafruit 上建立所需的 feeds 

### 步驟說明 
1. 使用 Keil uVision 或其他軟體，將 `uart-and-oled.c` 編譯為 HEX 可執行檔 
2. 使用 STC-ISP v6.91M 等燒錄軟體，將 HEX 檔燒錄至 8051 開發板 
3. 使用 Thonny 將 `uart-and-mqtt.py` 上傳並執行於 ESP32 
4. 使用 IoT MQTT 傳送城市名稱至 ESP32 
5. 等待 ESP32 擷取並傳送資料，即可於 OLED 上顯示天氣資訊
