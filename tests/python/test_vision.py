"""
Unit tests for litrun multi-modal vision subsystem, RTSP ingestion, and motion detection.
"""

import os
import tempfile
from litrun.vision import (
    is_network_stream,
    is_camera_device,
    capture_frame,
    compute_frame_motion_delta,
    VisionMotionDetector,
    format_detection_prompt,
    parse_detected_objects,
)


def test_network_stream_and_device_heuristics():
    assert is_network_stream("rtsp://192.168.1.100:554/live") is True
    assert is_network_stream("http://camera.local/mjpeg") is True
    assert is_network_stream("https://example.com/stream") is True
    assert is_network_stream("/dev/video0") is False

    assert is_camera_device("/dev/video0") is True
    assert is_camera_device("/dev/video2") is True
    assert is_camera_device("0") is True
    assert is_camera_device("frame.jpg") is False


def test_frame_capture_synthetic_fallback():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_jpg = os.path.join(tmpdir, "captured.jpg")
        success = capture_frame("/dev/video99", out_jpg)
        assert success is True
        assert os.path.isfile(out_jpg)
        with open(out_jpg, "rb") as f:
            hdr = f.read(2)
            assert hdr == b"\xff\xd8"


def test_motion_detector_thresholding():
    detector = VisionMotionDetector(threshold=0.08)

    frame1 = b"\xff\xd8" + bytes([50] * 512) + b"\xff\xd9"
    frame2 = b"\xff\xd8" + bytes([50] * 512) + b"\xff\xd9"
    frame3 = b"\xff\xd8" + bytes([220] * 512) + b"\xff\xd9"

    # Frame 1: initial baseline
    m1, d1 = detector.check_motion(frame1)
    assert m1 is True
    assert d1 == 1.0

    # Frame 2: identical
    m2, d2 = detector.check_motion(frame2)
    assert m2 is False
    assert d2 == 0.0

    # Frame 3: significant motion
    m3, d3 = detector.check_motion(frame3)
    assert m3 is True
    assert d3 > 0.08


def test_bounding_box_parsing():
    sample_json = (
        'Here is the analysis:\n'
        '{\n'
        '  "objects": [\n'
        '    {"label": "forklift", "box_2d": [100, 150, 400, 500], "confidence": 0.95},\n'
        '    {"label": "pallet", "box_2d": [410, 120, 480, 250], "confidence": 0.88}\n'
        '  ]\n'
        '}'
    )
    boxes = parse_detected_objects(sample_json)
    assert len(boxes) == 2
    assert boxes[0]["label"] == "forklift"
    assert boxes[0]["box_2d"] == [100, 150, 400, 500]
    assert boxes[1]["label"] == "pallet"

