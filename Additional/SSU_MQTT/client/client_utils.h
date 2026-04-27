#ifndef CLIENT_H
#define CLIENT_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <mosquitto.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define BROADCAST_PORT 54545
#define BROADCAST_MAGIC "MQTT_BROKER:"

#define MQTT_PORT 1883
#define MQTT_TOPIC "lichee_rv/stats"
#define KEEPALIVE 60
#endif

static char* discover_broker() {
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("UDP socket error");
        return NULL;
    }

    // Allow broadcast messages
    int broadcast_enable = 1;
    setsockopt(sock, SOL_SOCKET, SO_BROADCAST, &broadcast_enable, sizeof(broadcast_enable));

    // Configure reciever address
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(BROADCAST_PORT);
    addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("UDP bind error");
        close(sock);
        return NULL;
    }

    printf("Listening for broker broadcasts...\n");
    char buffer[256];
    int len = recv(sock, buffer, sizeof(buffer) - 1, 0);
    close(sock);

    if (len <= 0) {
        perror("UDP receive error");
        return NULL;
    }

    buffer[len] = '\0';
    printf("Received broadcast: %s\n", buffer);

    // Verify that messagw from broker
    if (strstr(buffer, BROADCAST_MAGIC) != buffer) {
        fprintf(stderr, "Invalid broadcast message\n");
        return NULL;
    }

    // Parsing ip and port from format "MQTT_BROKER:IP:PORT")
    char* ip = buffer + strlen(BROADCAST_MAGIC);
    char* port_str = strchr(ip, ':');
    if (!port_str) {
        fprintf(stderr, "Invalid broadcast format\n");
        return NULL;
    }

    *port_str = '\0';  // Split ip and port
    int port = atoi(port_str + 1);

    return strdup(ip);
}

static float get_cpu_usage() {
    FILE* fp = fopen("/proc/stat", "r");
    if (!fp) return -1;

    unsigned long user, nice, system, idle;
    fscanf(fp, "cpu %lu %lu %lu %lu", &user, &nice, &system, &idle); // read cpu info
    fclose(fp);

    unsigned long total = user + nice + system + idle;
    static unsigned long prev_total = 0, prev_idle = 0;

    float usage = 0.0;
    if (prev_total > 0) {
        float diff_idle = idle - prev_idle;
        float diff_total = total - prev_total;
        usage = 100.0 * (1.0 - diff_idle / diff_total); // calculate cpu usage
    }

    prev_total = total;
    prev_idle = idle;
    return usage;
}

static float get_ram_usage() {
    FILE* fp = fopen("/proc/meminfo", "r");
    if (!fp) return -1;

    char line[128];
    unsigned long total = 0, free = 0;

    while (fgets(line, sizeof(line), fp)) {
        if (strstr(line, "MemTotal:")) sscanf(line, "MemTotal: %lu kB", &total);
        if (strstr(line, "MemFree:")) sscanf(line, "MemFree: %lu kB", &free);
    }
    fclose(fp);

    if (total == 0) return -1;
    return 100.0 * (total - free) / total;
}
