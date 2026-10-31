#include <stdio.h>
#include <assert.h>
#include <string.h>
#include "jetson_adapter.h"

int main(void) {
    printf("[TEST] Running C NVIDIA Jetson Adapter Probe...\n");

    litrun_jetson_info_t info;
    int rc = litrun_jetson_probe(&info);
    assert(rc == 0);

    printf("  ✓ Jetson Probe Executed: available=%d, soc=%s, cuda_cores=%d, nvdla=%d\n",
           info.is_available, info.soc, info.cuda_cores, info.has_nvdla);

    char json_buf[512];
    int json_rc = litrun_jetson_to_json(&info, json_buf, sizeof(json_buf));
    assert(json_rc > 0);
    assert(strstr(json_buf, "\"cuda_cores\":") != NULL);

    printf("  ✓ Jetson JSON Output verified:\n%s\n", json_buf);
    printf("[TEST] All C Jetson Adapter Tests Passed!\n");
    return 0;
}
