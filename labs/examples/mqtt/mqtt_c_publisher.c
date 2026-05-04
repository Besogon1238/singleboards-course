#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <mosquitto.h>

#define MQTT_HOST   "localhost"
#define MQTT_PORT   1883
#define MQTT_TOPIC  "lichee/stats"
#define KEEPALIVE   60

static float get_cpu_usage(void) {
    FILE *fp = fopen("/proc/stat", "r");
    if (!fp) return -1;

    unsigned long user, nice, system, idle;
    fscanf(fp, "cpu %lu %lu %lu %lu", &user, &nice, &system, &idle);
    fclose(fp);

    unsigned long total = user + nice + system + idle;
    static unsigned long prev_total = 0, prev_idle = 0;
    float usage = 0.0;

    if (prev_total > 0) {
        float diff_idle  = idle - prev_idle;
        float diff_total = total - prev_total;
        usage = 100.0 * (1.0 - diff_idle / diff_total);
    }
    prev_total = total;
    prev_idle  = idle;
    return usage;
}

static float get_ram_usage(void) {
    FILE *fp = fopen("/proc/meminfo", "r");
    if (!fp) return -1;

    unsigned long total = 0, available = 0;
    char line[128];
    while (fgets(line, sizeof(line), fp)) {
        if (strstr(line, "MemTotal:"))
            sscanf(line, "MemTotal: %lu kB", &total);
        if (strstr(line, "MemAvailable:"))
            sscanf(line, "MemAvailable: %lu kB", &available);
    }
    fclose(fp);
    return (total > 0) ? 100.0 * (total - available) / total : -1;
}

int main(void) {
    mosquitto_lib_init();

    struct mosquitto *mosq = mosquitto_new(NULL, true, NULL);
    if (!mosq) {
        fprintf(stderr, "Error: mosquitto_new failed\n");
        return 1;
    }

    if (mosquitto_connect(mosq, MQTT_HOST, MQTT_PORT, KEEPALIVE)) {
        fprintf(stderr, "Error: cannot connect to broker\n");
        mosquitto_destroy(mosq);
        mosquitto_lib_cleanup();
        return 1;
    }

    printf("C MQTT publisher started.\n");
    printf("Publishing to '%s'. Press Ctrl+C to stop.\n", MQTT_TOPIC);

    char payload[128];
    while (1) {
        float cpu = get_cpu_usage();
        float ram = get_ram_usage();

        if (cpu < 0 || ram < 0) {
            fprintf(stderr, "Error reading system stats\n");
            sleep(1);
            continue;
        }

        snprintf(payload, sizeof(payload),
                 "{\"cpu\":%.1f,\"ram\":%.1f}", cpu, ram);

        int ret = mosquitto_publish(mosq, NULL, MQTT_TOPIC,
                                    strlen(payload), payload, 0, false);
        if (ret != MOSQ_ERR_SUCCESS)
            fprintf(stderr, "Publish error: %s\n", mosquitto_strerror(ret));
        else
            printf("Sent: %s\n", payload);

        sleep(2);
    }

    mosquitto_destroy(mosq);
    mosquitto_lib_cleanup();
    return 0;
}
