import json
import time
import socket

devices = {}

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("lichee_rv/stats")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        print(f"Raw message received: {payload}")
        data = json.loads(payload)
        devices[msg.topic] = data
        print(f"Parsed data: {data}") 
    except Exception as e:
        print(f"Error processing message: {e}")


def get_local_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))  # Google DNS
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception as e:
        print(f"Error getting IP: {e}")
        return "127.0.0.1"


def broadcast_broker_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    BROADCAST_PORT = 54545

    current_ip = get_local_ip()
    message = f"MQTT_BROKER:{current_ip}:1883".encode()
    
    while True:
        try:
            # Отправляем на широковещательный адрес
            sock.sendto(message, ('255.255.255.255', BROADCAST_PORT))
            print(f"[UDP] Sent broadcast: {message.decode()}")
        except Exception as e:
            print(f"[UDP] Broadcast error: {e}")
        time.sleep(5) 
