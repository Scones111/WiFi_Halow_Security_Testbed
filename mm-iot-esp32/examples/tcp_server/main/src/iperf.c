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
 * Minimal lwIP TCP Client
 * Morse Micro / lwIP compatible
 */

#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

#include "mm_app_common.h"
#include "mmwlan.h"                    // Morse Micro
#include "mmipal.h"                    // Morse Micro
#include "mmosal.h"                    // Morse Micro

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

static const char *TAG = "TCP_CLIENT";

static void tcp_client_task(void *pvParameters)
{
    char *server_ip = "10.51.33.100";     // ← CHANGE TO YOUR SERVER IP
    const int server_port = 5001;

    while (mmwlan_get_sta_state() != MMWLAN_STA_CONNECTED) {
        vTaskDelay(pdMS_TO_TICKS(500));
    }

    ESP_LOGI(TAG, "Connected to Wi-Fi. Starting TCP Client...");

    while (1) {   // Reconnect loop
        int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
        if (sock < 0) {
            ESP_LOGE(TAG, "Unable to create socket: errno %d", errno);
            vTaskDelay(pdMS_TO_TICKS(1000));
            continue;
        }

        struct sockaddr_in dest_addr;
        dest_addr.sin_family = AF_INET;
        dest_addr.sin_port = htons(server_port);
        inet_pton(AF_INET, server_ip, &dest_addr.sin_addr);

        ESP_LOGI(TAG, "Connecting to %s:%d ...", server_ip, server_port);

        if (connect(sock, (struct sockaddr *)&dest_addr, sizeof(dest_addr)) < 0) {
            ESP_LOGE(TAG, "Connection failed: errno %d", errno);
            close(sock);
            vTaskDelay(pdMS_TO_TICKS(2000));
            continue;
        }

        ESP_LOGI(TAG, "Successfully connected to server!");

        // Send and receive loop
        while (1) {
            // Send data
            char tx_buffer[128];
            snprintf(tx_buffer, sizeof(tx_buffer), "Hello from Morse Micro Client!\n");
            send(sock, tx_buffer, strlen(tx_buffer), 0);

            // Receive response
            char rx_buffer[512];
            int len = recv(sock, rx_buffer, sizeof(rx_buffer) - 1, 0);
            if (len <= 0) {
                ESP_LOGI(TAG, "Server disconnected");
                break;
            }

            rx_buffer[len] = '\0';
            ESP_LOGI(TAG, "Server replied: %s", rx_buffer);

            vTaskDelay(pdMS_TO_TICKS(2000));   // Send every 2 seconds
        }

        close(sock);
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

void app_main(void)
{
    printf("\n\nMorse Iperf Demo (Built " __DATE__ " " __TIME__ ")\n\n");

    /* Initialize and connect to Wi-Fi, blocks till connected */
    app_wlan_init();
    app_wlan_start();

    mmwlan_set_power_save_mode(MMWLAN_PS_DISABLED);

    printf("Link is up, proceeding to start TCP client\n");

    xTaskCreate(tcp_client_task, "tcp_client", 8192, NULL, 5, NULL);

}
