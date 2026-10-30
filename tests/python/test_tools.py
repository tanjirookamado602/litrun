"""
Unit tests for litrun embedded GPIO tools and tool dispatcher.
"""

from click.testing import CliRunner
from litrun.cli.main import cli
from litrun.tools.gpio import (
    GPIOController,
    gpio_write,
    gpio_read,
    get_hardware_telemetry,
)
from litrun.tools.dispatcher import (
    parse_tool_call,
    execute_embedded_tool,
    EMBEDDED_TOOLS,
)


def test_gpio_controller_mock_simulation():
    ctrl = GPIOController(mock=True)

    # Test pin write
    res_w = ctrl.write_pin(18, 1)
    assert res_w["success"] is True
    assert res_w["pin"] == 18
    assert res_w["state"] == 1
    assert res_w["mode"] == "simulation"

    # Test pin read back
    res_r = ctrl.read_pin(18)
    assert res_r["success"] is True
    assert res_r["pin"] == 18
    assert res_r["state"] == 1

    # Test pin write 0
    ctrl.write_pin(18, 0)
    res_r0 = ctrl.read_pin(18)
    assert res_r0["state"] == 0


def test_hardware_telemetry():
    telem = get_hardware_telemetry()
    assert "cpu_temp_celsius" in telem
    assert isinstance(telem["cpu_temp_celsius"], float)
    assert "load_average_1m" in telem
    assert "thermal_state" in telem
    assert telem["thermal_state"] in ["nominal", "throttled"]


def test_parse_tool_call_formats():
    # 1. Direct standard format
    raw1 = '{"tool": "gpio_write", "parameters": {"pin": 21, "value": 1}}'
    parsed1 = parse_tool_call(raw1)
    assert parsed1 is not None
    assert parsed1[0] == "gpio_write"
    assert parsed1[1] == {"pin": 21, "value": 1}

    # 2. Markdown fenced json block
    raw2 = '```json\n{"tool": "gpio_read", "parameters": {"pin": 4}}\n```'
    parsed2 = parse_tool_call(raw2)
    assert parsed2 is not None
    assert parsed2[0] == "gpio_read"
    assert parsed2[1] == {"pin": 4}

    # 3. OpenAI function calling format
    raw3 = '{"name": "get_hardware_telemetry", "arguments": {}}'
    parsed3 = parse_tool_call(raw3)
    assert parsed3 is not None
    assert parsed3[0] == "get_hardware_telemetry"
    assert parsed3[1] == {}


def test_execute_embedded_tool():
    res_write = execute_embedded_tool("gpio_write", {"pin": 17, "value": 1})
    assert res_write["success"] is True
    assert res_write["pin"] == 17

    res_read = execute_embedded_tool("gpio_read", {"pin": 17})
    assert res_read["success"] is True
    assert res_read["pin"] == 17

    res_telem = execute_embedded_tool("get_hardware_telemetry", {})
    assert "cpu_temp_celsius" in res_telem

    res_unknown = execute_embedded_tool("unknown_sensor", {})
    assert res_unknown["success"] is False
    assert "Unknown tool" in res_unknown["error"]


def test_cli_run_with_tools():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "--demo",
            "--tools",
            "-p",
            "Turn on the cooling fan connected to GPIO pin 18",
        ],
    )
    assert result.exit_code == 0
    assert "Embedded Tools: Active" in result.output
    assert "⚡ Hardware Action:" in result.output
    assert "✓ Hardware Result:" in result.output
    assert "gpio_write" in result.output

