"""
Unit tests for litrun edge quantization engine and memory footprint estimation.
"""

import os
import math
import random
import tempfile
from click.testing import CliRunner
from litrun.quantize import (
    quantize_f32_to_q8_0,
    dequantize_q8_0,
    quantize_f32_to_q4_0,
    dequantize_q4_0,
    quantize_weights,
    calculate_metrics,
    estimate_ram_footprint,
    save_litquant,
    load_litquant,
    QUANT_TYPE_Q8_0,
    QUANT_TYPE_Q4_0,
)
from litrun.cli.main import cli


def test_q8_0_quantization_accuracy():
    # 64 float weights
    weights = [math.sin(i * 0.1) * 2.5 for i in range(64)]

    data = quantize_f32_to_q8_0(weights)
    assert len(data) == (64 // 32) * 34  # 68 bytes

    deq = dequantize_q8_0(data, len(weights))
    assert len(deq) == 64

    # Max reconstruction error should be very small (< 0.03 for Q8)
    for orig, rec in zip(weights, deq):
        assert abs(orig - rec) < 0.03


def test_q4_0_quantization_accuracy():
    # 96 float weights
    weights = [math.cos(i * 0.15) * 1.8 for i in range(96)]

    data = quantize_f32_to_q4_0(weights)
    assert len(data) == (96 // 32) * 18  # 54 bytes

    deq = dequantize_q4_0(data, len(weights))
    assert len(deq) == 96

    metrics = calculate_metrics(weights, deq, QUANT_TYPE_Q4_0, len(data))
    assert metrics.compression_ratio > 5.0  # FP32 (384 bytes) to Q4_0 (54 bytes) = 7.1x
    assert metrics.psnr_db > 25.0


def test_ram_footprint_estimation():
    res = estimate_ram_footprint("smollm2-135m")
    assert res["model"] == "smollm2-135m"
    assert res["parameters"] == 135_000_000
    assert len(res["schemes"]) >= 4

    q4 = next(s for s in res["schemes"] if s["type"] == "Q4_0")
    assert q4["weights_mb"] < 120
    assert q4["rpi4_2gb_safe"] is True
    assert q4["opi5_16gb_safe"] is True


def test_litquant_binary_io():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "weights.litquant")
        tensors = {
            "model.embed_tokens.weight": ("Q8_0", [0.1 * i for i in range(32)]),
            "model.layers.0.mlp.gate_proj.weight": ("Q4_0", [-0.2 * i for i in range(64)]),
        }

        saved_size = save_litquant(out_path, tensors)
        assert os.path.isfile(out_path)
        assert saved_size > 0

        loaded = load_litquant(out_path)
        assert loaded["version"] == 1
        assert loaded["n_tensors"] == 2
        assert "model.embed_tokens.weight" in loaded["tensors"]
        assert loaded["tensors"]["model.embed_tokens.weight"]["quant_type"] == "Q8_0"


def test_cli_quantize_commands():
    runner = CliRunner()

    # Estimation
    res_est = runner.invoke(cli, ["quantize", "--estimate", "smollm2-135m"])
    assert res_est.exit_code == 0
    assert "Memory Envelope" in res_est.output

    # JSON Estimation
    res_json = runner.invoke(cli, ["quantize", "--estimate", "qwen2.5-0.5b", "--json"])
    assert res_json.exit_code == 0
    assert "schemes" in res_json.output

    # Quantize synthetic weights with verification
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "model_q4.litquant")
        res_q = runner.invoke(cli, ["quantize", "dummy.bin", "-t", "q4_0", "-o", out_file, "--verify"])
        assert res_q.exit_code == 0
        assert "Quantized Size" in res_q.output
        assert "Reconstruction PSNR" in res_q.output
        assert os.path.isfile(out_file)
