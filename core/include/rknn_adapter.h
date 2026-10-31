/*
 * litrun - Rockchip RKNN NPU Hardware Acceleration Adapter
 * Lightweight C99 interface for Rockchip RK3588, RK3588S, RK3566, and RK3568 NPUs.
 */

#ifndef LITRUN_RKNN_ADAPTER_H
#define LITRUN_RKNN_ADAPTER_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int is_available;
    char driver_version[64];
    char soc[32];
    int npu_cores;
    float peak_tops;
    int cur_freq_mhz;
} litrun_rknn_info_t;

/**
 * Probes the local Linux host for Rockchip NPU hardware, kernel drivers,
 * and devfreq properties (/dev/rknpu, /proc/rknpu/version, /sys/class/devfreq).
 */
int litrun_rknn_probe(litrun_rknn_info_t *info);

/**
 * Returns formatted JSON string describing NPU state.
 */
int litrun_rknn_to_json(const litrun_rknn_info_t *info, char *buffer, size_t max_len);

#ifdef __cplusplus
}
#endif

#endif /* LITRUN_RKNN_ADAPTER_H */

