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


#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>


static const char *TAG = "TCP_SERVER";

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
        int client_sock = accept(listen_sock, (struct sockaddr *)&client_addr, &addr_len);

        if (client_sock < 0) {
            ESP_LOGE(TAG, "Accept failed: errno %d", errno);
            continue;
        }


        char addr_str[32];
        inet_ntoa_r(((struct sockaddr_in *)&client_addr)->sin_addr, addr_str, sizeof(addr_str));
        ESP_LOGI(TAG, "Client connected from %s", addr_str);

        while (1) {

            if(mmwlan_get_sta_state() != MMWLAN_STA_CONNECTED){
                ESP_LOGI(TAG, "Wi-Fi disconnected, closing client socket");
                goto cleanup;
            }
            char rx_buffer[512];

            int len = recv(client_sock, rx_buffer, sizeof(rx_buffer) - 1, 0);

            if (len < 0) {
                ESP_LOGE(TAG, "recv failed: errno %d", errno);
                break;
            } else if (len == 0) {
                ESP_LOGI(TAG, "Client disconnected");
                break;
            } else {
                rx_buffer[len] = '\0';
                ESP_LOGI(TAG, "Received %d bytes: %s", len, rx_buffer);
                
                // Echo back
                send(client_sock, "OK\n", 3, 0);
            }
        }

        close(client_sock);
        ESP_LOGI(TAG, "Client disconnected");
    }
cleanup:
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
}