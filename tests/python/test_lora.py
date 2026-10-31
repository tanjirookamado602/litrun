"""
Unit tests for litrun On-Device LoRA adaptation
"""

import os
import tempfile
from click.testing import CliRunner
from litrun.cli.main import cli
from litrun.lora import LoRALayer, LoRAAdapter


def test_lora_layer_forward_and_backward():
    layer = LoRALayer(in_dim=16, out_dim=16, rank=2, alpha=4.0)
    x = [1.0] * 16
    # Initial forward should produce 0.0 because B is initialized to 0
    y_init = layer.forward(x)
    assert len(y_init) == 16
    assert all(abs(val) < 1e-9 for val in y_init)

    # Train step towards target
    target = [0.5] * 16
    loss1 = layer.train_step(x, target, lr=0.01)
    assert loss1 > 0.0

    # After step, B should no longer be all zero, and loss should decrease
    loss2 = layer.train_step(x, target, lr=0.01)
    assert loss2 < loss1


def test_lora_adapter_lifecycle_and_serialization():
    adapter = LoRAAdapter.create("test_adapter", base_model="smollm2-135m", rank=2, alpha=4.0)
    summary = adapter.get_summary()
    assert summary["name"] == "test_adapter"
    assert summary["rank"] == 2
    assert summary["trainable_parameters"] > 0
    assert summary["memory_footprint_kb"] > 0.0

    # Train on mock examples
    examples = [
        ("turn on cooling pump", "action: set_gpio(18, 1)"),
        ("turn off cooling pump", "action: set_gpio(18, 0)"),
    ]
    res = adapter.train_on_examples(examples, epochs=2, lr=0.01)
    assert res["epochs"] == 2
    assert res["examples_count"] == 2
    assert "final_loss" in res

    # Save and reload
    with tempfile.NamedTemporaryFile(suffix=".litlora", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        adapter.save(tmp_path)
        loaded = LoRAAdapter.load(tmp_path)
        assert loaded.config.adapter_name == "test_adapter"
        assert loaded.config.rank == 2
        assert len(loaded.layers) == len(adapter.layers)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_cli_lora_commands():
    runner = CliRunner()
    with tempfile.NamedTemporaryFile(suffix=".litlora", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Init
        res_init = runner.invoke(cli, ["lora", "init", "-n", "cli_test", "-o", tmp_path, "-r", "2"])
        assert res_init.exit_code == 0
        assert "Initialized Edge LoRA Adapter" in res_init.output

        # Info
        res_info = runner.invoke(cli, ["lora", "info", "-a", tmp_path])
        assert res_info.exit_code == 0
        assert "cli_test" in res_info.output

        # Train
        res_train = runner.invoke(cli, ["lora", "train", "-a", tmp_path, "--epochs", "2"])
        assert res_train.exit_code == 0
        assert "Training Complete" in res_train.output
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
