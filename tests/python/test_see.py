"""
Unit tests for litrun see (Vision-Language Model execution).
"""

import os
from click.testing import CliRunner
from litrun.cli.main import cli
from litrun.registry import get_model, list_models


def test_vlm_registry_entries():
    smol = get_model("smolvlm-256m")
    assert smol is not None
    assert smol.multimodal is True
    assert smol.family == "smolvlm"

    moon = get_model("moondream2")
    assert moon is not None
    assert moon.multimodal is True
    assert moon.family == "moondream"


def test_cli_see_demo():
    runner = CliRunner()
    result = runner.invoke(cli, ["see", "--demo", "-p", "Inspect camera sensor"])
    assert result.exit_code == 0
    assert "litrun vision:" in result.output
    assert "SmolVLM" in result.output
    assert "Visual Inspection" in result.output


def test_cli_see_custom_image():
    runner = CliRunner()
    test_img = "/tmp/test_litrun_unit_img.jpg"
    with open(test_img, "wb") as f:
        f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xd9")

    try:
        result = runner.invoke(cli, ["see", test_img, "--demo", "-p", "Check test image"])
        assert result.exit_code == 0
        assert "litrun vision:" in result.output
        assert "test_litrun_unit_img.jpg" in result.output
    finally:
        if os.path.exists(test_img):
            os.remove(test_img)
