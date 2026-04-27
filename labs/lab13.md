# Лабораторная №13. Протокол MQTT и IoT-системы

## Цель работы

Освоить принципы работы протокола MQTT для построения IoT-систем, научиться настраивать MQTT-брокер и создавать клиентские приложения. Интегрировать систему сбора данных с датчиков (лабораторная №12) в распределённую IoT-систему с использованием MQTT-протокола.

## Подготовительный материал

### Что такое MQTT?

MQTT (Message Queuing Telemetry Transport) — это лёгкий протокол обмена сообщениями, разработанный специально для IoT-устройств с ограниченными ресурсами. Основные особенности:

- **Издатель-подписчик (Pub/Sub)**: Клиенты публикуют сообщения в топики, другие клиенты подписываются на топики
- **Лёгкий протокол**: Минимальный оверхед, подходит для устройств с ограниченной памятью и пропускной способностью
- **Качество обслуживания (QoS)**: Три уровня гарантии доставки сообщений
- **Сохраняемые сессии**: Брокер может хранить сообщения для отключённых клиентов
- **Безопасность**: Поддержка TLS/SSL и аутентификации

### Архитектура MQTT

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Publisher  │────▶│   Broker    │────▶│ Subscriber  │
│  (Arduino)  │     │  (Lichee)   │     │  (Web App)  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
   Публикует           Хранит и           Получает
   в топик:           перенаправляет     сообщения
   "sensors/data"     сообщения          из топика
```

### Основные компоненты

1. **Брокер (Broker)**: Центральный сервер, который принимает сообщения от издателей и отправляет их подписчикам
2. **Издатель (Publisher)**: Клиент, который отправляет сообщения в топики
3. **Подписчик (Subscriber)**: Клиент, который получает сообщения из топиков
4. **Топик (Topic)**: Иерархическая структура для организации сообщений (например: `home/livingroom/temperature`)

### Качество обслуживания (QoS)

- **QoS 0**: "At most once" — сообщение отправляется один раз, без подтверждения
- **QoS 1**: "At least once" — сообщение гарантированно доставляется, возможны дубликаты
- **QoS 2**: "Exactly once" — сообщение доставляется ровно один раз (самый надёжный, но медленный)

## Практическая часть

### Задание 1: Установка и настройка MQTT-брокера на Lichee RV Dock

1. Установите MQTT-брокер Mosquitto:

```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
```

2. Проверьте статус службы:

```bash
sudo systemctl status mosquitto
```

3. Запустите брокер, если он не запущен:

```bash
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

4. Проверьте работу брокера, отправив тестовое сообщение:

```bash
# В первом терминале - подписчик
mosquitto_sub -h localhost -t "test/topic"

# Во втором терминале - издатель
mosquitto_pub -h localhost -t "test/topic" -m "Hello MQTT!"
```

### Задание 2: Создание MQTT-клиента на Python

Создайте файл `mqtt_client.py`:

```python
import paho.mqtt.client as mqtt
import json
import time
import random

# Конфигурация
BROKER = "localhost"
PORT = 1883
TOPIC_PUBLISH = "sensors/data"
TOPIC_SUBSCRIBE = "sensors/control"

# Callback при подключении
def on_connect(client, userdata, flags, rc):
    print(f"Подключено с кодом: {rc}")
    client.subscribe(TOPIC_SUBSCRIBE)
    print(f"Подписан на топик: {TOPIC_SUBSCRIBE}")

# Callback при получении сообщения
def on_message(client, userdata, msg):
    print(f"Получено сообщение: {msg.topic} -> {msg.payload.decode()}")

# Callback при публикации
def on_publish(client, userdata, mid):
    print(f"Сообщение опубликовано (mid: {mid})")

# Создание клиента
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish

# Подключение
client.connect(BROKER, PORT, 60)
client.loop_start()

try:
    while True:
        # Генерация тестовых данных
        sensor_data = {
            "temperature": round(random.uniform(20.0, 25.0), 2),
            "humidity": round(random.uniform(40.0, 60.0), 2),
            "pressure": round(random.uniform(980.0, 1020.0), 2),
            "timestamp": time.time()
        }
        
        # Публикация данных
        result = client.publish(
            TOPIC_PUBLISH,
            json.dumps(sensor_data),
            qos=1
        )
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Опубликовано: {sensor_data}")
        else:
            print(f"Ошибка публикации: {result.rc}")
        
        time.sleep(5)
        
except KeyboardInterrupt:
    print("\nОстановка клиента...")
    client.loop_stop()
    client.disconnect()
```

### Задание 3: Интеграция с системой сбора данных

Модифицируйте код из лабораторной №12 для отправки данных через MQTT:

```python
# Файл: lichee_system_mqtt.py
import paho.mqtt.client as mqtt
import json
import time
from lichee_system import LicheeSystem

class MQTTLicheeSystem(LicheeSystem):
    def __init__(self):
        super().__init__()
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.connect("localhost", 1883, 60)
        self.mqtt_client.loop_start()
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        print(f"MQTT подключен с кодом: {rc}")
        client.subscribe("sensors/control")
    
    def process_sensor_data(self, data):
        # Обработка данных от Arduino
        processed_data = super().process_sensor_data(data)
        
        # Отправка через MQTT
        mqtt_message = {
            "source": "arduino_bme280",
            "data": processed_data,
            "timestamp": time.time(),
            "location": "lab_room"
        }
        
        self.mqtt_client.publish(
            "sensors/arduino/data",
            json.dumps(mqtt_message),
            qos=1
        )
        
        return processed_data
    
    def cleanup(self):
        super().cleanup()
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()

if __name__ == "__main__":
    system = MQTTLicheeSystem()
    
    try:
        print("Система MQTT-Lichee запущена")
        print("Данные будут публиковаться в топик: sensors/arduino/data")
        print("Для остановки нажмите Ctrl+C")
        
        while True:
            # Чтение данных от Arduino
            data = system.read_from_spi()
            if data:
                system.process_sensor_data(data)
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nОстановка системы...")
        system.cleanup()
```

### Задание 4: Создание веб-интерфейса для мониторинга

Создайте простой веб-интерфейс для отображения данных:

```python
# Файл: mqtt_web_monitor.py
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import json
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Хранилище данных
sensor_data = {
    'temperature': [],
    'humidity': [],
    'pressure': []
}

# MQTT Callback
def on_mqtt_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        
        # Сохранение данных
        for key in ['temperature', 'humidity', 'pressure']:
            if key in data.get('data', {}):
                sensor_data[key].append(data['data'][key])
                # Ограничение истории
                if len(sensor_data[key]) > 100:
                    sensor_data[key].pop(0)
        
        # Отправка через WebSocket
        socketio.emit('sensor_update', data)
        
    except Exception as e:
        print(f"Ошибка обработки MQTT: {e}")

# Запуск MQTT-клиента в отдельном потоке
def start_mqtt_client():
    client = mqtt.Client()
    client.on_message = on_mqtt_message
    client.connect("localhost", 1883, 60)
    client.subscribe("sensors/arduino/data")
    client.loop_forever()

# Маршруты Flask
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    return jsonify(sensor_data)

@app.route('/api/latest')
def get_latest():
    latest = {}
    for key in sensor_data:
        if sensor_data[key]:
            latest[key] = sensor_data[key][-1]
    return jsonify(latest)

if __name__ == '__main__':
    # Запуск MQTT-клиента в фоне
    mqtt_thread = threading.Thread(target=start_mqtt_client, daemon=True)
    mqtt_thread.start()
    
    # Запуск веб-сервера
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
```

Создайте HTML-шаблон `templates/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>IoT Monitor - Лабораторная №13</title>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .cards { display: flex; gap: 20px; margin-bottom: 30px; }
        .card { flex: 1; padding: 20px; border-radius: 8px; background: #f5f5f5; }
        .chart-container { margin-bottom: 30px; }
        h1 { color: #333; }
        .value { font-size: 24px; font-weight: bold; }
        .unit { color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>IoT Monitor - Данные с датчика BME280</h1>
        
        <div class="cards">
            <div class="card" id="temp-card">
                <h3>Температура</h3>
                <div class="value" id="temp-value">--</div>
                <div class="unit">°C</div>
            </div>
            <div class="card" id="hum-card">
                <h3>Влажность</h3>
                <div class="value" id="hum-value">--</div>
                <div class="unit">%</div>
            </div>
            <div class="card" id="press-card">
                <h3>Давление</h3>
                <div class="value" id="press-value">--</div>
                <div class="unit">hPa</div>
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="sensorChart"></canvas>
        </div>
        
        <div id="log"></div>
    </div>
    
    <script>
        const socket = io();
        const ctx = document.getElementById('sensorChart').getContext('2d');
        
        let chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Температура (°C)',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        yAxisID: 'y'
                    },
                    {
                        label: 'Влажность (%)',
                        data: [],
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        yAxisID: 'y1'
                    },
                    {
                        label: 'Давление (hPa)',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        yAxisID: 'y2'
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Время'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Температура (°C)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Влажность (%)'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    },
                    y2: {
                        type: 'linear',
                        display: false,
                        position: 'right'
                    }
                }
            }
        });
        
        // Обработка MQTT сообщений через WebSocket
        socket.on('sensor_update', function(data) {
            const sensorData = data.data;
            const timestamp = new Date().toLocaleTimeString();
            
            // Обновление значений
            document.getElementById('temp-value').textContent = 
                sensorData.temperature ? sensorData.temperature.toFixed(1) : '--';
            document.getElementById('hum-value').textContent = 
                sensorData.humidity ? sensorData.humidity.toFixed(1) : '--';
            document.getElementById('press-value').textContent = 
                sensorData.pressure ? sensorData.pressure.toFixed(1) : '--';
            
            // Обновление графика
            chart.data.labels.push(timestamp);
            chart.data.datasets[0].data.push(sensorData.temperature);
            chart.data.datasets[1].data.push(sensorData.humidity);
            chart.data.datasets[2].data.push(sensorData.pressure);
            
            // Ограничение количества точек
            if (chart.data.labels.length > 20) {
                chart.data.labels.shift();
                chart.data.datasets.forEach(dataset => dataset.data.shift());
            }
            
            chart.update();
            
            // Логирование
            const log = document.getElementById('log');
            const logEntry = document.createElement('div');
            logEntry.textContent = `[${timestamp}] Получены данные: T=${sensorData.temperature}°C, H=${sensorData.humidity}%, P=${sensorData.pressure}hPa`;
            log.prepend(logEntry);
            
            if (log.children.length > 10) {
                log.removeChild(log.lastChild);
            }
        });
        
        // Загрузка исторических данных
        fetch('/api/latest')
            .then(response => response.json())
            .then(data => {
                if (data.temperature) {
                    document.getElementById('temp-value').textContent = data.temperature.toFixed(1);
                }
                if (data.humidity) {
                    document.getElementById('hum-value').textContent = data.humidity.toFixed(1);
                }
                if (data.pressure) {
                    document.getElementById('press-value').textContent = data.pressure.toFixed(1);
                }
            });
    </script>
</body>
</html>
```

### Задание 5: Создание MQTT-клиента для Arduino

Добавьте MQTT-поддержку в код Arduino для прямой публикации данных:

```cpp
// Файл: arduino_mqtt_client.ino
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_BME280.h>

// Настройки WiFi
const char* ssid = "your_SSID";
const char* password = "your_PASSWORD";

// Настройки MQTT
const char* mqtt_server = "192.168.1.100"; // IP Lichee RV Dock
const int mqtt_port = 1883;
const char* mqtt_topic = "sensors/arduino/raw";

WiFiClient espClient;
PubSubClient client(espClient);
Adafruit_BME280 bme;

unsigned long lastMsg = 0;
#define MSG_BUFFER_SIZE (50)
char msg[MSG_BUFFER_SIZE];

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Подключение к ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi подключен");
  Serial.print("IP адрес: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Попытка подключения к MQTT...");
    
    String clientId = "ArduinoClient-";
    clientId += String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println("подключено");
      client.publish("sensors/status", "Arduino подключен");
    } else {
      Serial.print("ошибка, rc=");
      Serial.print(client.state());
      Serial.println(" повтор через 5 секунд");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  // Инициализация BME280
  if (!bme.begin(0x76)) {
    Serial.println("Не удалось найти датчик BME280!");
    while (1);
  }
  
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > 5000) {
    lastMsg = now;
    
    // Чтение данных с датчика
    float temperature = bme.readTemperature();
    float humidity = bme.readHumidity();
    float pressure = bme.readPressure() / 100.0F;
    
    // Формирование JSON сообщения
    String jsonMsg = "{";
    jsonMsg += "\"temperature\":" + String(temperature, 2) + ",";
    jsonMsg += "\"humidity\":" + String(humidity, 2) + ",";
    jsonMsg += "\"pressure\":" + String(pressure, 2);
    jsonMsg += "}";
    
    // Публикация в MQTT
    Serial.print("Публикация: ");
    Serial.println(jsonMsg);
    client.publish(mqtt_topic, jsonMsg.c_str());
    
    // Также отправка по SPI (для обратной совместимости)
    Serial1.print(jsonMsg);
  }
}
```

## Задание для самостоятельной работы

1. **Базовая задача**: Разверните MQTT-брокер на Lichee RV Dock и создайте простого клиента, который публикует тестовые данные.

2. **Средняя задача**: Интегрируйте систему из лабораторной №12 с MQTT, чтобы данные с Arduino передавались не только по SPI, но и публиковались в MQTT-брокер.

3. **Продвинутая задача**: Создайте веб-интерфейс для мониторинга данных в реальном времени с использованием WebSocket и MQTT.

4. **Дополнительная задача**: Реализуйте систему управления, где веб-интерфейс может отправлять команды Arduino через MQTT (например, включить/выключить светодиод).

## Контрольные вопросы

1. В чём преимущества архитектуры "издатель-подписчик" по сравнению с клиент-серверной архитектурой для IoT-систем?
2. Какие уровни QoS существуют в MQTT и в каких сценариях каждый из них целесообразно использовать?
3. Как обеспечивается безопасность в MQTT? Какие механизмы аутентификации и шифрования поддерживаются?
4. Чем отличается MQTT от других протоколов для IoT, таких как CoAP или HTTP/2?
5. Как организовать иерархию топиков для системы умного дома с множеством датчиков и устройств?
6. Какие проблемы могут возникнуть при использовании MQTT в сетях с нестабильным соединением и как их решить?
7. Как масштабировать MQTT-инфраструктуру при увеличении количества устройств?
8. В чём преимущества использования MQTT поверх WebSocket для веб-приложений?
9. Как реализовать retained messages и will messages в MQTT и для чего они используются?
10. Какие библиотеки для работы с MQTT существуют для различных платформ (Arduino, Python, JavaScript)?

## Дополнительные материалы

1. **Официальная документация MQTT**: https://mqtt.org/
2. **Документация Mosquitto**: https://mosquitto.org/documentation/
3. **Библиотека Paho MQTT для Python**: https://github.com/eclipse/paho.mqtt.python
4. **Библиотека PubSubClient для Arduino**: https://github.com/knolleary/pubsubclient
5. **MQTT Explorer** (визуальный клиент): http://mqtt-explorer.com/
6. **Статья "MQTT Essentials"**: https://www.hivemq.com/mqtt-essentials/

## Примечания

- Для работы MQTT необходимо, чтобы устройства были в одной сети
- При использовании WiFi на Arduino убедитесь в стабильности соединения
- Для production-систем рекомендуется использовать TLS/SSL шифрование
- MQTT-брокер можно развернуть не только на Lichee, но и на облачных платформах (AWS IoT, Azure IoT Hub, etc.)
- Веб-интерфейс можно разместить на том же Lichee RV Dock или на отдельном сервере