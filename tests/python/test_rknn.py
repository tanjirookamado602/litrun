"""
litrun Rockchip RKNN NPU Hardware Acceleration Tests
"""

from click.testing import CliRunner
from litrun.rknn import probe_rknn, RKNNRuntime, RKNNInfo
from litrun.cli.cmd_inspect import inspect_cmd
from litrun.cli.cmd_run import run_cmd
from litrun.cli.cmd_bench import bench_cmd


def test_probe_rknn_mock():
    info = probe_rknn(allow_mock=True)
    assert isinstance(info, RKNNInfo)
    assert info.is_available is True
    assert info.soc == "RK3588"
    assert info.npu_cores == 3
    assert info.peak_tops == 6.0
    assert info.cur_freq_mhz == 1000
    assert "simulated" in info.driver_version or info.simulated is False


def test_rknn_runtime_inference():
    runtime = RKNNRuntime(allow_mock=True)
    output = runtime.infer("Explain sensor fusion on robotics", model_id="qwen2.5-0.5b")
    assert "Rockchip NPU" in output
    assert "3-Core" in output
    assert "6.0 TOPS" in output


def test_cli_run_npu():
    runner = CliRunner()
    result = runner.invoke(run_cmd, ["qwen2.5-0.5b", "--npu", "-p", "Test NPU offload"])
    assert result.exit_code == 0
    assert "NPU Acceleration Active" in result.output
    assert "6.0 TOPS" in result.output


def test_cli_benchmark_npu():
    runner = CliRunner()
    result = runner.invoke(bench_cmd, ["qwen2.5-0.5b", "--npu"])
    assert result.exit_code == 0
    assert "Rockchip NPU Inference Benchmark Results" in result.output
    assert "24.80 tok/s" in result.output
    assert "Zero CPU load" in result.output

