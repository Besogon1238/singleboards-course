#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import json
import time

TOPIC = "lichee/stats"
INTERVAL = 2.0

def get_cpu_usage():
    """Возвращает загрузку CPU в процентах (от 0 до 100)."""
    with open("/proc/stat") as f:
        fields = f.readline().split()
    user, nice, system, idle = map(int, fields[1:5])
    total = user + nice + system + idle

    if not hasattr(get_cpu_usage, "prev"):
        get_cpu_usage.prev = (total, idle)
        return 0.0

    prev_total, prev_idle = get_cpu_usage.prev
    get_cpu_usage.prev = (total, idle)

    diff_total = total - prev_total
    diff_idle  = idle - prev_idle
    return 100.0 * (1.0 - diff_idle / diff_total) if diff_total > 0 else 0.0

def get_ram_usage():
    """Возвращает использование RAM в процентах (от 0 до 100)."""
    total = free = 0
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemTotal:"):
                total = int(line.split()[1])
            elif line.startswith("MemAvailable:"):
                free = int(line.split()[1])
    return 100.0 * (total - free) / total if total > 0 else 0.0

def main():
    client = mqtt.Client()
    client.connect("localhost", 1883)
    client.loop_start()

    print(f"Publishing to '{TOPIC}' every {INTERVAL}s. Ctrl+C to stop.")
    try:
        while True:
            cpu = get_cpu_usage()
            ram = get_ram_usage()
            payload = json.dumps({"cpu": round(cpu, 1), "ram": round(ram, 1)})
            client.publish(TOPIC, payload)
            print(f"Published: {payload}")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
