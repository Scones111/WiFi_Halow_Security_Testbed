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
#include "esp_system.h"
#include "esp_timer.h"
#include "esp_heap_caps.h"

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

#define TCP_SERVER_IP "10.51.33.100"            // ← CHANGE TO YOUR SERVER IP
#define CENTRALIZED_LOG_SERVER "192.168.0.101"  // ← CHANGE TO YOUR DEVICE IP

static const char *TAG = "TCP_CLIENT";
volatile uint32_t tcp_disconnect_count = 0;
static const char *TAG_TEMP = "TEMP_SENSOR";

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
            // ESP32 has IDLE0 and IDLE1 for both cores
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

#define ADC_UNIT        ADC_UNIT_1
#define ADC_CHANNEL     ADC_CHANNEL_5 // Changed from ADC_CHANNEL_0 (GPIO1) to ADC_CHANNEL_5 (GPIO6) to avoid pin conflict with Morse Micro chip

static void tcp_client_task(void *pvParameters)
{
    // Server config
    char *server_ip = TCP_SERVER_IP;
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

    int udp_metrics_sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
    if (udp_metrics_sock < 0) {
        ESP_LOGE(TAG, "Unable to create UDP metrics socket: errno %d", errno);
    }
    struct sockaddr_in udp_dest_addr;
    memset(&udp_dest_addr, 0, sizeof(udp_dest_addr));
    udp_dest_addr.sin_family = AF_INET;
    udp_dest_addr.sin_port = htons(5005);
    inet_pton(AF_INET, CENTRALIZED_LOG_SERVER, &udp_dest_addr.sin_addr);

    // TCP reconnect loop
    bool first_connect = true;
    while (1) {
        int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
        if (sock < 0) {
            ESP_LOGE(TAG, "Unable to create socket: errno %d", errno);
            vTaskDelay(pdMS_TO_TICKS(1000));
            continue;
        }

        struct timeval timeout;
        timeout.tv_sec = 3;
        timeout.tv_usec = 0;
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
        setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));

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
        
        if (!first_connect) {
            tcp_disconnect_count++;
        }
        first_connect = false;

        // Start measurement loop
        while (1) {
            // Measure temperaturew;
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
            if (len < 0) {
                if (errno == EAGAIN || errno == EWOULDBLOCK) {
                    ESP_LOGE(TAG, "Server receive timeout");
                } else {
                    ESP_LOGE(TAG, "recv failed: errno %d", errno);
                }
                break; // Break inner loop to trigger reconnect
            } else if (len == 0) {
                ESP_LOGI(TAG, "Server disconnected");
                break; // Break inner loop to trigger reconnect
            }

            rx_buffer[len] = '\0';
            ESP_LOGI(TAG, "Server replied: %s", rx_buffer);

            int64_t end_time = esp_timer_get_time();
            uint32_t free_heap = esp_get_free_heap_size();
            uint32_t total_heap = heap_caps_get_total_size(MALLOC_CAP_DEFAULT);
            float ram_used_percent = ((float)(total_heap - free_heap) / (float)total_heap) * 100.0f;
            float cpu_used_percent = get_cpu_usage_percent();
            
            uint32_t tcp_disconnects = tcp_disconnect_count;

            ESP_LOGI("ML_DATA", "Timestamp: %lld, CPU_Used: %.2f%%, RAM_Used: %.2f%%, TCP_Disconnects: %lu", 
                     end_time, cpu_used_percent, ram_used_percent, tcp_disconnects);

            if (udp_metrics_sock >= 0) {
                char udp_buf[256];
                snprintf(udp_buf, sizeof(udp_buf), 
                         "{\"device\": \"client\", \"esp32_uptime_us\": %lld, \"cpu_used_pct\": %.2f, \"ram_used_pct\": %.2f, \"tcp_disconnects\": %lu}", 
                         end_time, cpu_used_percent, ram_used_percent, tcp_disconnects);
                int sent = sendto(udp_metrics_sock, udp_buf, strlen(udp_buf), 0, (struct sockaddr *)&udp_dest_addr, sizeof(udp_dest_addr));
                if (sent < 0) {
                    ESP_LOGE(TAG, "UDP sendto failed: errno %d", errno);
                } else {
                    ESP_LOGI(TAG, "UDP packet sent (%d bytes) to %s:5005", sent, CENTRALIZED_LOG_SERVER);
                }
            }

            vTaskDelay(pdMS_TO_TICKS(5000));   // Read and send every 5 seconds
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
