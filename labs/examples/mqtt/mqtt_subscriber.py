#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import json

# IP-адрес Lichee RV Dock (узнайте командой "hostname -I" на Lichee)
BROKER = "192.168.1.50"
TOPIC  = "lichee/stats"

def on_connect(client, userdata, flags, rc):
    print(f"Connected to broker (rc={rc})")
    client.subscribe(TOPIC)
    print(f"Subscribed to '{TOPIC}'")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        cpu = data.get("cpu", "?")
        ram = data.get("ram", "?")
        print(f"CPU: {cpu:5.1f}%   RAM: {ram:5.1f}%")
    except json.JSONDecodeError:
        print(f"Raw: {msg.payload.decode()}")

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, 1883)
    print(f"Connected to MQTT broker at {BROKER}")
    print("Listening for messages...")
    client.loop_forever()

if __name__ == "__main__":
    main()
