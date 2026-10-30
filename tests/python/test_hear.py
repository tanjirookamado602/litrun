"""
Unit tests for litrun hear (Edge speech recognition and audio perception).
"""

import os
from click.testing import CliRunner
from litrun.cli.main import cli
from litrun.cli.cmd_hear import create_mock_wav_header


def test_create_mock_wav_header():
    tmp_wav = "/tmp/test_unit_audio_header.wav"
    try:
        create_mock_wav_header(tmp_wav)
        assert os.path.exists(tmp_wav)
        assert os.path.getsize(tmp_wav) > 1000  # valid WAV header + samples
        with open(tmp_wav, "rb") as f:
            header = f.read(12)
            assert header.startswith(b"RIFF")
            assert header.endswith(b"WAVE")
    finally:
        if os.path.exists(tmp_wav):
            os.remove(tmp_wav)


def test_cli_hear_demo():
    runner = CliRunner()
    result = runner.invoke(cli, ["hear", "--demo"])
    assert result.exit_code == 0
    assert "litrun hear:" in result.output
    assert "whisper-tiny.en" in result.output


def test_cli_hear_custom_audio_file():
    runner = CliRunner()
    test_wav = "/tmp/test_unit_clip.wav"
    create_mock_wav_header(test_wav)

    try:
        result = runner.invoke(cli, ["hear", test_wav, "--demo"])
        assert result.exit_code == 0
        assert "litrun hear:" in result.output
    finally:
        if os.path.exists(test_wav):
            os.remove(test_wav)


def test_cli_hear_pipe_run():
    runner = CliRunner()
    result = runner.invoke(cli, ["hear", "--demo", "--pipe-run", "--tools"])
    assert result.exit_code == 0
    assert "Routing transcription to litrun autonomous engine" in result.output
    assert "Embedded Tools: Active" in result.output
    assert "Hardware Action:" in result.output
