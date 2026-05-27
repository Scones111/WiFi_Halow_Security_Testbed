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

#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"

static const char *TAG = "TCP_CLIENT";
static const char *TAG_TEMP = "TEMP_SENSOR";

#define ADC_UNIT        ADC_UNIT_1
#define ADC_CHANNEL     ADC_CHANNEL_5 // Changed from ADC_CHANNEL_0 (GPIO1) to ADC_CHANNEL_5 (GPIO6) to avoid pin conflict with Morse Micro chip

static void tcp_client_task(void *pvParameters)
{
    // Server config
    char *server_ip = "10.51.33.100";     // ← CHANGE TO YOUR SERVER IP
    const int server_port = 5001;

    // Wait for Wi-Fi
    while (mmwlan_get_sta_state() != MMWLAN_STA_CONNECTED) {
        vTaskDelay(pdMS_TO_TICKS(500));
    }

    ESP_LOGI(TAG, "Connected to Wi-Fi. Starting TCP Client...");

    // ADC init
    adc_oneshot_unit_handle_t adc1_handle;
    adc_oneshot_unit_init_cfg_t init_config1 = {
        .unit_id = ADC_UNIT,
    };
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&init_config1, &adc1_handle));

    // ADC config
    adc_oneshot_chan_cfg_t config = {
        .bitwidth = ADC_BITWIDTH_DEFAULT,
        .atten = ADC_ATTEN_DB_11, // 11dB attenuation for 0 ~ 3.1V range
    };
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc1_handle, ADC_CHANNEL, &config));

    // ADC calibration
    adc_cali_handle_t adc1_cali_handle = NULL;
    bool do_calibration = false;

#if ADC_CALI_SCHEME_CURVE_FITTING_SUPPORTED
    adc_cali_curve_fitting_config_t cali_config = {
        .unit_id = ADC_UNIT,
        .chan = ADC_CHANNEL,
        .atten = ADC_ATTEN_DB_11,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    esp_err_t ret = adc_cali_create_scheme_curve_fitting(&cali_config, &adc1_cali_handle);
    if (ret == ESP_OK) {
        do_calibration = true;
    }
#elif ADC_CALI_SCHEME_LINE_FITTING_SUPPORTED
    adc_cali_line_fitting_config_t cali_config = {
        .unit_id = ADC_UNIT,
        .atten = ADC_ATTEN_DB_11,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    esp_err_t ret = adc_cali_create_scheme_line_fitting(&cali_config, &adc1_cali_handle);
    if (ret == ESP_OK) {
        do_calibration = true;
    }
#endif

    if (!do_calibration) {
        ESP_LOGW(TAG, "ADC calibration scheme not supported on this platform!");
    }

    ESP_LOGI(TAG, "ADC Initialized. Starting TCP Client loop...");

    // TCP reconnect loop
    while (1) {
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
            int adc_raw;
            int voltage = 0;
            float temperature = 0.0;

            ESP_ERROR_CHECK(adc_oneshot_read(adc1_handle, ADC_CHANNEL, &adc_raw));
            ESP_LOGI(TAG_TEMP, "ADC%d Channel[%d] Raw Data: %d", ADC_UNIT + 1, ADC_CHANNEL, adc_raw);

            if (do_calibration) {
                ESP_ERROR_CHECK(adc_cali_raw_to_voltage(adc1_cali_handle, adc_raw, &voltage));
                ESP_LOGI(TAG_TEMP, "ADC%d Channel[%d] Cali Voltage: %d mV", ADC_UNIT + 1, ADC_CHANNEL, voltage);
                
                // LM35 outputs 10mV per degree Celsius (e.g., 250mV = 25.0 °C)
                temperature = voltage / 10.0;
                ESP_LOGI(TAG_TEMP, "Temperature: %.2f °C", temperature);
            } else {
                // Uncalibrated approximation (assuming 12-bit ADC and ~3.3V ref with 12dB attenuation)
                voltage = (adc_raw * 3300) / 4095;
                temperature = voltage / 10.0;
                ESP_LOGI(TAG_TEMP, "Uncalibrated Temperature: %.2f °C", temperature);
            }

            // Send data
            char tx_buffer[128];
            snprintf(tx_buffer, sizeof(tx_buffer), "Temperature: %.2f C\n", temperature);
            int err = send(sock, tx_buffer, strlen(tx_buffer), 0);
            if (err < 0) {
                ESP_LOGE(TAG, "send failed: errno %d", errno);
                break; // Break inner loop to trigger reconnect
            }

            // Receive response
            char rx_buffer[512];
            int len = recv(sock, rx_buffer, sizeof(rx_buffer) - 1, 0);
            if (len <= 0) {
                ESP_LOGI(TAG, "Server disconnected");
                break; // Break inner loop to trigger reconnect
            }

            rx_buffer[len] = '\0';
            ESP_LOGI(TAG, "Server replied: %s", rx_buffer);

            vTaskDelay(pdMS_TO_TICKS(2000));   // Read and send every 2 seconds
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
