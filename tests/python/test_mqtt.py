"""
litrun Industrial MQTT Edge Sensor Daemon & Autonomous IoT Agent Unit Tests
"""

import json
from click.testing import CliRunner

from litrun.mqtt import (
    encode_mqtt_string,
    build_mqtt_connect_packet,
    build_mqtt_publish_packet,
    MQTTTelemetryAgent,
)
from litrun.cli.cmd_mqtt import mqtt_cmd


def test_packet_builders():
    # Test string encoder
    encoded = encode_mqtt_string("test")
    assert encoded[:2] == b"\x00\x04"
    assert encoded[2:] == b"test"

    # Test connect packet
    conn = build_mqtt_connect_packet("client123")
    assert conn[0] == 0x10  # CONNECT packet type
    assert b"MQTT" in conn
    assert b"client123" in conn

    # Test publish packet
    pub = build_mqtt_publish_packet("sensors/temp", '{"value": 42}')
    assert pub[0] == 0x30  # PUBLISH QoS 0
    assert b"sensors/temp" in pub
    assert b'{"value": 42}' in pub


def test_agent_telemetry_reasoning():
    agent = MQTTTelemetryAgent(mock=True)
    assert agent.connect() is True

    # Test nominal sensor
    nominal = agent.evaluate_telemetry({"sensor": "coolant_temp", "value": 45.2, "unit": "C"})
    assert nominal["status"] == "NOMINAL"
    assert nominal["action_required"] == "NOMINAL_MONITORING"

    # Test temperature anomaly
    overheat = agent.evaluate_telemetry({"sensor": "motor_temp", "value": 84.5, "unit": "C"})
    assert overheat["status"] == "CRITICAL_ANOMALY"
    assert overheat["action_required"] == "TRIGGER_COOLING_FAN"
    assert "exceeded safe thermal limit" in overheat["reasoning"]

    # Test vibration anomaly
    vibe = agent.evaluate_telemetry({"sensor": "bearing_vibration", "value": 9.2, "unit": "mm/s"})
    assert vibe["status"] == "CRITICAL_ANOMALY"
    assert vibe["action_required"] == "EMERGENCY_SHUTDOWN"

    # Test pressure anomaly
    press = agent.evaluate_telemetry({"sensor": "hydraulic_pressure", "value": 11.5, "unit": "PSI"})
    assert press["status"] == "CRITICAL_ANOMALY"
    assert press["action_required"] == "ISOLATE_VALVE"

    # Test publish alert
    assert agent.publish_alert(overheat) is True
    agent.close()


def test_cli_mqtt_demo():
    runner = CliRunner()
    result = runner.invoke(mqtt_cmd, ["--demo"])
    assert result.exit_code == 0
    assert "Industrial MQTT Edge Agent" in result.output
    assert "CRITICAL" in result.output
    assert "TRIGGER_COOLING" in result.output
    assert "factory/alerts" in result.output
