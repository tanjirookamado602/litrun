"""
litrun NVIDIA Jetson Hardware Acceleration Unit Tests
"""

from click.testing import CliRunner
from litrun.jetson import probe_jetson, JetsonRuntime, JetsonInfo
from litrun.cli.cmd_run import run_cmd
from litrun.cli.cmd_bench import bench_cmd


def test_probe_jetson_mock():
    info = probe_jetson(allow_mock=True)
    assert isinstance(info, JetsonInfo)
    assert info.is_available is True
    assert "Tegra" in info.soc
    assert info.cuda_cores == 1024
    assert info.has_nvdla is True
    assert info.nvdla_engines == 2


def test_jetson_runtime_inference():
    runtime = JetsonRuntime(allow_mock=True)
    out = runtime.infer("Explain robot trajectory planning", model_id="qwen2.5-0.5b")
    assert "NVIDIA Jetson" in out
    assert "CUDA Cores" in out
    assert "NVDLA" in out


def test_cli_run_gpu():
    runner = CliRunner()
    result = runner.invoke(run_cmd, ["qwen2.5-0.5b", "--gpu", "-p", "Test Jetson GPU"])
    assert result.exit_code == 0
    assert "NVIDIA Jetson Active" in result.output
    assert "1024 CUDA Cores" in result.output


def test_cli_benchmark_gpu():
    runner = CliRunner()
    result = runner.invoke(bench_cmd, ["qwen2.5-0.5b", "--gpu"])
    assert result.exit_code == 0
    assert "NVIDIA Jetson Inference Benchmark Results" in result.output
    assert "28.50 tok/s" in result.output
