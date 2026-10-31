/*
 * litrun - NVIDIA Jetson GPU & NVDLA Acceleration Adapter
 * Lightweight C99 interface for NVIDIA Jetson Orin Nano, Orin NX, AGX Orin, and Xavier.
 */

#ifndef LITRUN_JETSON_ADAPTER_H
#define LITRUN_JETSON_ADAPTER_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int is_available;
    char soc[32];
    int cuda_cores;
    int has_nvdla;
    int nvdla_engines;
    char jetpack_version[32];
} litrun_jetson_info_t;

/**
 * Probes the local Linux host for NVIDIA Tegra hardware, CUDA nodes,
 * NVDLA engines, and JetPack L4T releases.
 */
int litrun_jetson_probe(litrun_jetson_info_t *info);

/**
 * Formats Jetson device status as JSON.
 */
int litrun_jetson_to_json(const litrun_jetson_info_t *info, char *buffer, size_t max_len);

#ifdef __cplusplus
}
#endif

#endif /* LITRUN_JETSON_ADAPTER_H */
