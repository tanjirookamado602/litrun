"""
litrun Automated Benchmark Suite & JSON Performance Reports Unit Tests
"""

import json
import os
import tempfile
from click.testing import CliRunner

from litrun.benchmark import (
    run_single_benchmark,
    run_benchmark_matrix,
    run_backend_comparison,
    BenchmarkReport,
    BenchmarkResult,
)
from litrun.cli.cmd_bench import bench_cmd


def test_run_single_benchmark_cpu():
    res = run_single_benchmark(model_id="smollm2-135m", tokens=16, backend="cpu", allow_mock=True)
    assert isinstance(res, BenchmarkResult)
    assert res.model_id == "smollm2-135m"
    assert res.backend == "cpu"
    assert res.throughput_tok_s > 0
    assert res.ttft_ms >= 0
    assert res.memory_mb > 0
    d = res.to_dict()
    assert "throughput_tok_s" in d
    assert "ttft_ms" in d


def test_run_single_benchmark_accelerators():
    # NPU
    res_npu = run_single_benchmark(model_id="qwen2.5-0.5b", tokens=32, backend="npu", allow_mock=True)
    assert res_npu.backend == "rknn_npu"
    assert res_npu.throughput_tok_s == 24.80
    assert res_npu.ttft_ms == 28.4

    # GPU
    res_gpu = run_single_benchmark(model_id="qwen2.5-0.5b", tokens=32, backend="gpu", allow_mock=True)
    assert res_gpu.backend == "jetson_cuda"
    assert res_gpu.throughput_tok_s == 28.50
    assert res_gpu.ttft_ms == 21.2


def test_run_benchmark_matrix():
    report = run_benchmark_matrix(model_ids=["smollm2-135m", "smollm2-360m"], tokens=16, backend="cpu", allow_mock=True)
    assert isinstance(report, BenchmarkReport)
    assert len(report.results) == 2
    assert report.results[0].model_id == "smollm2-135m"
    assert report.results[1].model_id == "smollm2-360m"
    assert "board_name" in report.hardware


def test_run_backend_comparison():
    report = run_backend_comparison(model_id="qwen2.5-0.5b", tokens=16, allow_mock=True)
    assert len(report.results) == 3
    backends = [r.backend for r in report.results]
    assert "cpu" in backends
    assert "rknn_npu" in backends
    assert "jetson_cuda" in backends


def test_benchmark_json_export():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        report = run_backend_comparison(model_id="qwen2.5-0.5b", tokens=16, allow_mock=True)
        report.save_json(tmp_path)

        assert os.path.exists(tmp_path)
        with open(tmp_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "litrun_version" in data
        assert "timestamp" in data
        assert "hardware" in data
        assert len(data["results"]) == 3
        assert data["results"][0]["model_id"] == "qwen2.5-0.5b"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_cli_benchmark_export_json():
    runner = CliRunner()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        result = runner.invoke(bench_cmd, ["qwen2.5-0.5b", "-n", "16", "--export-json", tmp_path])
        assert result.exit_code == 0
        assert "Exported benchmark report" in result.output
        assert os.path.exists(tmp_path)

        with open(tmp_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data["results"]) == 1
        assert data["results"][0]["backend"] == "cpu"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_cli_benchmark_matrix_and_compare():
    runner = CliRunner()

    # Matrix
    res_matrix = runner.invoke(bench_cmd, ["--all", "-n", "16"])
    assert res_matrix.exit_code == 0
    assert "Multi-Model Inference Performance Matrix" in res_matrix.output
    assert "smollm2-135m" in res_matrix.output

    # Compare
    res_comp = runner.invoke(bench_cmd, ["--compare", "-n", "16"])
    assert res_comp.exit_code == 0
    assert "Hardware Accelerator Comparison Matrix" in res_comp.output
    assert "Rockchip NPU" in res_comp.output
    assert "NVIDIA Jetson" in res_comp.output
