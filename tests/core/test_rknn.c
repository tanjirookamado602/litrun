#include <stdio.h>
#include <assert.h>
#include <string.h>
#include "rknn_adapter.h"

int main(void) {
    printf("[TEST] Running C RKNN Adapter Probe...\n");

    litrun_rknn_info_t info;
    int rc = litrun_rknn_probe(&info);
    assert(rc == 0);

    printf("  ✓ RKNN Probe Executed successfully: available=%d, soc=%s, cores=%d, peak_tops=%.1f\n",
           info.is_available, info.soc, info.npu_cores, info.peak_tops);

    char json_buf[512];
    int json_rc = litrun_rknn_to_json(&info, json_buf, sizeof(json_buf));
    assert(json_rc > 0);
    assert(strstr(json_buf, "\"is_available\":") != NULL);
    assert(strstr(json_buf, "\"soc\":") != NULL);

    printf("  ✓ RKNN JSON Output verified:\n%s\n", json_buf);
    printf("[TEST] All C RKNN Adapter Tests Passed!\n");
    return 0;
}
