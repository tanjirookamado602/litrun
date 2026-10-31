#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include "jetson_adapter.h"

int litrun_jetson_probe(litrun_jetson_info_t *info) {
    if (!info) return -1;
    memset(info, 0, sizeof(litrun_jetson_info_t));

    struct stat st;
    int has_nvgpu = (stat("/dev/nvhost-gpu", &st) == 0 || stat("/dev/nvgpu", &st) == 0);
    int has_nvdla = (stat("/dev/nvhost-ctrl-nvdla", &st) == 0 || stat("/dev/nvhost-nvdla0", &st) == 0);

    /* Read JetPack L4T release info */
    char l4t_buf[64] = "none";
    FILE *f_tegra = fopen("/etc/nv_tegra_release", "r");
    if (f_tegra) {
        if (fgets(l4t_buf, sizeof(l4t_buf), f_tegra)) {
            char *hash = strchr(l4t_buf, '#');
            if (hash) {
                memmove(l4t_buf, hash + 1, strlen(hash));
            }
            char *comma = strchr(l4t_buf, ',');
            if (comma) *comma = '\0';
        }
        fclose(f_tegra);
    }

    /* Check devicetree compatible for Tegra SoC identification */
    char dt_buf[128] = {0};
    FILE *f_dt = fopen("/proc/device-tree/compatible", "r");
    if (f_dt) {
        size_t n = fread(dt_buf, 1, sizeof(dt_buf) - 1, f_dt);
        if (n > 0) dt_buf[n] = '\0';
        fclose(f_dt);
    }

    if (has_nvgpu || has_nvdla || strstr(dt_buf, "tegra234") != NULL || strstr(dt_buf, "tegra") != NULL) {
        info->is_available = 1;
        if (strstr(dt_buf, "tegra234") != NULL) {
            snprintf(info->soc, sizeof(info->soc), "Tegra Orin");
            info->cuda_cores = 1024;
            info->has_nvdla = 1;
            info->nvdla_engines = 2;
        } else if (strstr(dt_buf, "tegra194") != NULL) {
            snprintf(info->soc, sizeof(info->soc), "Tegra Xavier");
            info->cuda_cores = 512;
            info->has_nvdla = 1;
            info->nvdla_engines = 2;
        } else {
            snprintf(info->soc, sizeof(info->soc), "Tegra GPU");
            info->cuda_cores = 256;
            info->has_nvdla = has_nvdla ? 1 : 0;
            info->nvdla_engines = has_nvdla ? 1 : 0;
        }
        snprintf(info->jetpack_version, sizeof(info->jetpack_version), "%s", l4t_buf);
    } else {
        info->is_available = 0;
        snprintf(info->soc, sizeof(info->soc), "none");
        info->cuda_cores = 0;
        info->has_nvdla = 0;
        info->nvdla_engines = 0;
        snprintf(info->jetpack_version, sizeof(info->jetpack_version), "none");
    }

    return 0;
}

int litrun_jetson_to_json(const litrun_jetson_info_t *info, char *buffer, size_t max_len) {
    if (!info || !buffer || max_len == 0) return -1;

    return snprintf(buffer, max_len,
        "{\n"
        "  \"is_available\": %s,\n"
        "  \"soc\": \"%s\",\n"
        "  \"cuda_cores\": %d,\n"
        "  \"has_nvdla\": %s,\n"
        "  \"nvdla_engines\": %d,\n"
        "  \"jetpack_version\": \"%s\"\n"
        "}",
        info->is_available ? "true" : "false",
        info->soc,
        info->cuda_cores,
        info->has_nvdla ? "true" : "false",
        info->nvdla_engines,
        info->jetpack_version
    );
}
