import threading
import paho.mqtt.client as mqtt
from broker_utils import on_connect,on_message,get_local_ip,broadcast_broker_ip

threading.Thread(target=broadcast_broker_ip, daemon=True).start()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

broker_ip = get_local_ip()

try:
    client.connect(broker_ip, 1883, 60)
    print("Connecting to broker...")
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()
    print("Disconnected")
except Exception as e:
    print(f"Connection error: {e}")