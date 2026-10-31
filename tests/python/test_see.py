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


def test_vision_motion_detector_and_bounding_boxes():
    from litrun.vision import VisionMotionDetector, compute_frame_motion_delta, parse_detected_objects, format_detection_prompt

    frame_a = b"\xff\xd8" + bytes([10] * 200) + b"\xff\xd9"
    frame_b = b"\xff\xd8" + bytes([200] * 200) + b"\xff\xd9"
    delta = compute_frame_motion_delta(frame_a, frame_b)
    assert delta > 0.3

    detector = VisionMotionDetector(threshold=0.05)
    is_motion1, delta1 = detector.check_motion(frame_a)
    assert is_motion1 is True  # First frame trigger

    is_motion2, delta2 = detector.check_motion(frame_a)
    assert is_motion2 is False  # Identical frame -> no motion
    assert delta2 == 0.0

    prompt = format_detection_prompt("Locate obstacles")
    assert "schema" in prompt.lower()
    assert "box_2d" in prompt

    boxes = parse_detected_objects('{"objects": [{"label": "crate", "box_2d": [10, 20, 80, 90], "confidence": 0.95}]}')
    assert len(boxes) == 1
    assert boxes[0]["label"] == "crate"


def test_cli_see_detect_mode():
    runner = CliRunner()
    result = runner.invoke(cli, ["see", "--demo", "--detect", "--json"])
    assert result.exit_code == 0
    assert "objects" in result.output
    assert "industrial_robot" in result.output

