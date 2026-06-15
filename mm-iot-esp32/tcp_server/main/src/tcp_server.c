/*
 * Copyright 2022-2023 Morse Micro
 *
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * @file
 * @brief Throughput measurement using iperf.
 *
 * The Iperf parameters are specified using the defines in the file. Additional defines in
 * @c mm_app_loadconfig.c and @c mm_app_common.c are used to configure the network stack and WLAN
 * interface.
 *
 * @note It is assumed that you have followed the steps in the @ref GETTING_STARTED guide and are
 * therefore familiar with how to build, flash, and monitor an application using the MM-IoT-SDK
 * framework.
 *
 * This file demonstrates how to run iperf using the Morse Micro WLAN API.
 */


/*
 * Minimal lwIP TCP Server
 * Morse Micro / lwIP compatible
 */

#include "mm_app_common.h"
#include "mmosal.h"
#include "mmipal.h"
#include "mmwlan.h"
#include <string.h>
#include <stdio.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "esp_heap_caps.h"


#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define CENTRALIZED_LOG_SERVER "192.168.0.101"  // ← CHANGE TO YOUR DEVICE IP

static const char *TAG = "TCP_SERVER";
volatile uint32_t tcp_disconnect_count = 0;
static uint32_t bytes_received = 0;
static int64_t throughput_current_time = 0;
static float last_throughput_bps = 0.0f;

static float get_cpu_usage_percent(void)
{
    static uint32_t prev_total_run_time = 0;
    static uint32_t prev_idle_run_time = 0;

    uint32_t ulTotalRunTime;
    UBaseType_t uxArraySize = uxTaskGetNumberOfTasks();
    TaskStatus_t *pxTaskStatusArray = malloc(uxArraySize * sizeof(TaskStatus_t));
    float cpu_used_percent = 0.0f;

    if (pxTaskStatusArray != NULL) {
        uxArraySize = uxTaskGetSystemState(pxTaskStatusArray, uxArraySize, &ulTotalRunTime);
        uint32_t actual_total_time = 0;
        uint32_t idle_run_time = 0;
        for (UBaseType_t x = 0; x < uxArraySize; x++) {
            actual_total_time += pxTaskStatusArray[x].ulRunTimeCounter;
            if (strncmp(pxTaskStatusArray[x].pcTaskName, "IDLE", 4) == 0) {
                idle_run_time += pxTaskStatusArray[x].ulRunTimeCounter;
            }
        }
        free(pxTaskStatusArray);

        if (prev_total_run_time != 0 && actual_total_time > prev_total_run_time) {
            uint32_t total_delta = actual_total_time - prev_total_run_time;
            uint32_t idle_delta = idle_run_time - prev_idle_run_time;

            if (total_delta > 0) {
                cpu_used_percent = 100.0f - ((float)idle_delta / total_delta) * 100.0f;
            }
        }
        
        prev_total_run_time = actual_total_time;
        prev_idle_run_time = idle_run_time;
    }
    
    if (cpu_used_percent < 0.0f) cpu_used_percent = 0.0f;
    if (cpu_used_percent > 100.0f) cpu_used_percent = 100.0f;

    return cpu_used_percent;
}

static float get_throughput(void)
{
    int64_t currentTime = esp_timer_get_time();

    if (throughput_current_time == 0){
        throughput_current_time = currentTime;
        return 0.0f;
    }

    double elapsed_time = (currentTime - throughput_current_time) / 1000000.0;

    if (elapsed_time >= 5.0) {
        if (bytes_received > 0) {
            last_throughput_bps = (bytes_received * 8.0) / elapsed_time;
        } else {
            last_throughput_bps = 0.0f;
        }

        bytes_received = 0;
        throughput_current_time = currentTime;
    }

    return last_throughput_bps;
}

static void udp_metrics_task(void *pvParameters)
{
    // Wait until fully connected
    while (mmwlan_get_sta_state() != MMWLAN_STA_CONNECTED) {
        vTaskDelay(pdMS_TO_TICKS(500));
    }

    int udp_metrics_sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
    if (udp_metrics_sock < 0) {
        ESP_LOGE(TAG, "Unable to create UDP metrics socket: errno %d", errno);
        vTaskDelete(NULL);
        return;
    }

    struct sockaddr_in udp_dest_addr;
    memset(&udp_dest_addr, 0, sizeof(udp_dest_addr));
    udp_dest_addr.sin_family = AF_INET;
    udp_dest_addr.sin_port = htons(5005);
    inet_pton(AF_INET, CENTRALIZED_LOG_SERVER, &udp_dest_addr.sin_addr);

    ESP_LOGI(TAG, "Starting dedicated UDP metrics task to %s:5005", CENTRALIZED_LOG_SERVER);

    while (1) {
        if (mmwlan_get_sta_state() != MMWLAN_STA_CONNECTED) {
            vTaskDelay(pdMS_TO_TICKS(1000));
            continue;
        }

        int64_t end_time = esp_timer_get_time();
        uint32_t free_heap = esp_get_free_heap_size();
        uint32_t total_heap = heap_caps_get_total_size(MALLOC_CAP_DEFAULT);
        float ram_used_percent = ((float)(total_heap - free_heap) / (float)total_heap) * 100.0f;
        float cpu_used_percent = get_cpu_usage_percent();
        float throughput = get_throughput();
        uint32_t tcp_disconnects = tcp_disconnect_count;

        ESP_LOGI("ML_DATA", "Timestamp: %lld, CPU_Used: %.2f%%, RAM_Used: %.2f%%, Throughput: %.2f bps, TCP_Disconnects: %lu", 
                 end_time, cpu_used_percent, ram_used_percent, throughput, (unsigned long)tcp_disconnects);

        if (udp_metrics_sock >= 0) {
            char udp_buf[256];
            snprintf(udp_buf, sizeof(udp_buf), 
                     "{\"device\": \"server\", "
                     "\"esp32_uptime_us\": %lld, "
                     "\"cpu_used_pct\": %.2f, "
                     "\"ram_used_pct\": %.2f, "
                     "\"tcp_throughput_bps\": %.2f, "
                     "\"tcp_disconnects\": %lu}", 
                     end_time, cpu_used_percent, ram_used_percent, throughput, (unsigned long)tcp_disconnects);
            int sent = sendto(udp_metrics_sock, udp_buf, strlen(udp_buf), 0, (struct sockaddr *)&udp_dest_addr, sizeof(udp_dest_addr));
            if (sent < 0) {
                ESP_LOGE(TAG, "UDP sendto failed: errno %d", errno);
            } else {
                ESP_LOGI(TAG, "UDP packet sent (%d bytes) to %s:5005", sent, CENTRALIZED_LOG_SERVER);
            }
        }

        vTaskDelay(pdMS_TO_TICKS(5000));
    }
}


static void tcp_server_task(void *pvParameters)
{
    // Wait until fully connected and IP obtained
    while (mmwlan_get_sta_state() != MMWLAN_STA_CONNECTED) {
        vTaskDelay(pdMS_TO_TICKS(500));
    }
    struct mmipal_ip_config ip_config;

    if (mmipal_get_ip_config(&ip_config) == MMIPAL_SUCCESS) {

        printf("IP address: %s\n", ip_config.ip_addr);
    }

    ESP_LOGI(TAG, "Wi-Fi connected → Starting TCP Server on port 5001");

    int client_sock = -1;
    int listen_sock = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
    if (listen_sock < 0) {
        ESP_LOGE(TAG, "Unable to create socket: errno %d", errno);
        vTaskDelete(NULL);
        return;
    }

    struct sockaddr_in server_addr = {
        .sin_family = AF_INET,
        .sin_addr.s_addr = INADDR_ANY,
        .sin_port = htons(5001)               // ← Change port if needed
    };

    if (bind(listen_sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        ESP_LOGE(TAG, "Bind failed: errno %d", errno);
        goto cleanup;
    }

    if (listen(listen_sock, 5) < 0) {
        ESP_LOGE(TAG, "Listen failed: errno %d", errno);
        goto cleanup;
    }

    while (1) {
        struct sockaddr_storage client_addr;
        socklen_t addr_len = sizeof(client_addr);
        client_sock = accept(listen_sock, (struct sockaddr *)&client_addr, &addr_len);

        if (client_sock < 0) {
            ESP_LOGE(TAG, "Accept failed: errno %d", errno);
            vTaskDelay(pdMS_TO_TICKS(1000));
            continue;
        }

        int timeout_count = 0;

        struct timeval timeout;
        timeout.tv_sec = 3;
        timeout.tv_usec = 0;
        setsockopt(client_sock, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
        setsockopt(client_sock, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));

        char addr_str[32];
        inet_ntoa_r(((struct sockaddr_in *)&client_addr)->sin_addr, addr_str, sizeof(addr_str));
        ESP_LOGI(TAG, "Client connected from %s", addr_str);

        while (1) {

            if(mmwlan_get_sta_state() != MMWLAN_STA_CONNECTED){
                ESP_LOGI(TAG, "Wi-Fi disconnected, dropping client to wait for reconnect");
                break;
            }
            char rx_buffer[512];

            int len = recv(client_sock, rx_buffer, sizeof(rx_buffer) - 1, 0);

            if (len < 0) {
                if (errno == EAGAIN || errno == EWOULDBLOCK) {
                    timeout_count++;
                    if (timeout_count >= 3) {
                        ESP_LOGW(TAG, "Client timeout (9 seconds), dropping connection");
                        break;
                    }
                    continue; // Timeout, loop back to check Wi-Fi state
                }
                ESP_LOGE(TAG, "recv failed: errno %d", errno);
                break;
            } else if (len == 0) {
                ESP_LOGI(TAG, "Client disconnected");
                break;
            } else {
                timeout_count = 0; // reset timeout counter on successful read
                rx_buffer[len] = '\0';
                ESP_LOGI(TAG, "Received %d bytes: %s", len, rx_buffer);
                
                bytes_received += len;
                // Echo back
                send(client_sock, "OK\n", 3, 0);
            }
        }

        close(client_sock);
        client_sock = -1;
        ESP_LOGI(TAG, "Client disconnected");
        tcp_disconnect_count++;
    }
cleanup:
    if (client_sock >= 0) {
        close(client_sock);
    }
    close(listen_sock);
    vTaskDelete(NULL);
}

void app_main(void)
{
    printf("\n\nMorse Iperf Demo (Built " __DATE__ " " __TIME__ ")\n\n");

    /* Initialize and connect to Wi-Fi, blocks till connected */
    app_wlan_init();
    app_wlan_start();

    mmwlan_set_power_save_mode(MMWLAN_PS_DISABLED);

    xTaskCreate(tcp_server_task, "tcp_srv", 8192, NULL, 5, NULL);
    xTaskCreate(udp_metrics_task, "udp_metrics", 4096, NULL, 5, NULL);
}