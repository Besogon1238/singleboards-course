#include <stdio.h>
#include "client_utils.h"

int main() {

    char* broker_ip = discover_broker();
    if (!broker_ip) {
        fprintf(stderr, "Failed to discover broker\n");
        return 1;
    }

    printf("Discovered broker at %s\n", broker_ip);

    struct mosquitto *mosq = mosquitto_new(NULL, true, NULL);
    if (mosquitto_connect(mosq, broker_ip, MQTT_PORT, KEEPALIVE)) {
        fprintf(stderr, "MQTT connection failed\n");
        free(broker_ip);
        return 1;
    }

    char payload[128];
    float cpu, ram;

    mosquitto_lib_init();

    if (!mosq) {
        fprintf(stderr, "Error: Out of memory.\n");
        return 1;
    }

    if (mosquitto_connect(mosq, broker_ip, MQTT_PORT, KEEPALIVE)) {
        fprintf(stderr, "Unable to connect to MQTT broker.\n");
        return 1;
    }

    free(broker_ip);

    printf("MQTT client started. Press Ctrl+C to exit.\n");

    while (1) {
        cpu = get_cpu_usage();
        ram = get_ram_usage();

        if (cpu < 0 || ram < 0) {
            fprintf(stderr, "Error reading system stats\n");
            sleep(1);
            continue;
        }

        snprintf(payload, sizeof(payload),"{\"cpu\":%.2f,\"ram\":%.2f}", cpu, ram);

        int ret = mosquitto_publish(mosq, NULL, MQTT_TOPIC,strlen(payload), payload, 0, false);

        if (ret != MOSQ_ERR_SUCCESS) {
            fprintf(stderr, "Error publishing: %s\n", mosquitto_strerror(ret));
        } else {
            printf("Sent: %s\n", payload);
        }

        sleep(1);
    }

    mosquitto_destroy(mosq);
    mosquitto_lib_cleanup();
    return 0;
}
