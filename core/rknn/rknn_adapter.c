#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include "rknn_adapter.h"

static void safe_trim(char *str) {
    if (!str) return;
    size_t len = strlen(str);
    while (len > 0 && (str[len - 1] == '\n' || str[len - 1] == '\r' || str[len - 1] == ' ')) {
        str[len - 1] = '\0';
        len--;
    }
}

int litrun_rknn_probe(litrun_rknn_info_t *info) {
    if (!info) return -1;
    memset(info, 0, sizeof(litrun_rknn_info_t));

    struct stat st;
    int dev_found = (stat("/dev/rknpu", &st) == 0 || stat("/dev/rknpu0", &st) == 0);

    /* Read driver version if available */
    const char *version_paths[] = {
        "/proc/rknpu/version",
        "/sys/kernel/debug/rknpu/version",
        NULL
    };

    char driver_buf[64] = "not detected";
    for (int i = 0; version_paths[i] != NULL; i++) {
        FILE *f = fopen(version_paths[i], "r");
        if (f) {
            if (fgets(driver_buf, sizeof(driver_buf), f)) {
                safe_trim(driver_buf);
            }
            fclose(f);
            break;
        }
    }

    /* Check devicetree compatible for SoC identification */
    char dt_buf[128] = {0};
    FILE *f_dt = fopen("/proc/device-tree/compatible", "r");
    if (f_dt) {
        size_t n = fread(dt_buf, 1, sizeof(dt_buf) - 1, f_dt);
        if (n > 0) dt_buf[n] = '\0';
        fclose(f_dt);
    }

    if (dev_found || strstr(dt_buf, "rk3588") != NULL) {
        info->is_available = 1;
        snprintf(info->soc, sizeof(info->soc), "RK3588");
        info->npu_cores = 3;
        info->peak_tops = 6.0f;
        snprintf(info->driver_version, sizeof(info->driver_version), "%s", driver_buf);
    } else if (strstr(dt_buf, "rk3566") != NULL || strstr(dt_buf, "rk3568") != NULL) {
        info->is_available = 1;
        snprintf(info->soc, sizeof(info->soc), "RK3566/RK3568");
        info->npu_cores = 1;
        info->peak_tops = 1.0f;
        snprintf(info->driver_version, sizeof(info->driver_version), "%s", driver_buf);
    } else {
        info->is_available = 0;
        snprintf(info->soc, sizeof(info->soc), "none");
        info->npu_cores = 0;
        info->peak_tops = 0.0f;
        snprintf(info->driver_version, sizeof(info->driver_version), "none");
    }

    /* Check current NPU frequency */
    const char *freq_paths[] = {
        "/sys/class/devfreq/fdab0000.npu/cur_freq",
        "/sys/class/devfreq/fde40000.npu/cur_freq",
        NULL
    };

    info->cur_freq_mhz = 0;
    for (int i = 0; freq_paths[i] != NULL; i++) {
        FILE *ff = fopen(freq_paths[i], "r");
        if (ff) {
            long hz = 0;
            if (fscanf(ff, "%ld", &hz) == 1) {
                info->cur_freq_mhz = (int)(hz / 1000000);
            }
            fclose(ff);
            break;
        }
    }

    if (info->is_available && info->cur_freq_mhz == 0) {
        info->cur_freq_mhz = 1000; /* Standard active clock on RK3588 */
    }

    return 0;
}

int litrun_rknn_to_json(const litrun_rknn_info_t *info, char *buffer, size_t max_len) {
    if (!info || !buffer || max_len == 0) return -1;

    return snprintf(buffer, max_len,
        "{\n"
        "  \"is_available\": %s,\n"
        "  \"soc\": \"%s\",\n"
        "  \"npu_cores\": %d,\n"
        "  \"peak_tops\": %.1f,\n"
        "  \"cur_freq_mhz\": %d,\n"
        "  \"driver_version\": \"%s\"\n"
        "}",
        info->is_available ? "true" : "false",
        info->soc,
        info->npu_cores,
        info->peak_tops,
        info->cur_freq_mhz,
        info->driver_version
    );
}
