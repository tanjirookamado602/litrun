"""
Unit tests for litrun enterprise edge fleet management and cryptographic OTA updates.
"""

import os
import tempfile
from click.testing import CliRunner
from litrun.fleet import (
    FleetManager,
    FleetNodeProfile,
    OTAPackage,
    create_local_fleet_node,
)
from litrun.cli.main import cli


def test_ota_package_cryptographic_signing():
    pkg = OTAPackage(
        package_id="pkg-test-01",
        target_model="qwen2.5-0.5b",
        target_quant="q4_k_m",
        target_version="1.2.0",
        sha256_checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )

    secret = "edge-cluster-secret-key-123"
    pkg.signature = pkg.compute_signature(secret)
    assert len(pkg.signature) == 64
    assert pkg.verify_signature(secret) is True

    # Tampering test
    assert pkg.verify_signature("wrong-secret") is False
    pkg.target_version = "1.2.1"
    assert pkg.verify_signature(secret) is False


def test_fleet_manager_lifecycle_and_canary_promotion():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = FleetManager(storage_dir=tmpdir)

        # Enroll 3 nodes
        n1 = FleetNodeProfile("node-01", "rpi5-gateway", "Raspberry Pi 5", "BCM2712", 8192, 4096, 48.0, 0, "smollm2-135m", "1.0.0")
        n2 = FleetNodeProfile("node-02", "opi5-vision", "Orange Pi 5", "RK3588", 16384, 12000, 42.0, 0, "smollm2-135m", "1.0.0")
        n3 = FleetNodeProfile("node-03", "jetson-robot", "Jetson Orin Nano", "Orin", 8192, 5000, 52.0, 0, "smollm2-135m", "1.0.0")

        manager.enroll_node(n1)
        manager.enroll_node(n2)
        manager.enroll_node(n3)

        summary = manager.fleet_telemetry_summary()
        assert summary["total_nodes"] == 3
        assert summary["healthy_nodes"] == 3
        assert summary["total_ram_mb"] == 8192 + 16384 + 8192

        # Create Canary OTA Deployment
        pkg = OTAPackage("pkg-ota-99", "smollm2-360m", "q4_k_m", "2.0.0", "abc123sha", rollout_strategy="canary", canary_ratio=0.34)
        rollout = manager.create_ota_deployment(pkg)

        assert rollout.phase == "canary_active"
        assert len(rollout.canary_nodes) == 1
        canary_id = rollout.canary_nodes[0]
        assert manager.nodes[canary_id].current_model == "smollm2-360m"

        # Evaluate healthy canary -> promote to all
        success, msg = manager.evaluate_canary("pkg-ota-99")
        assert success is True
        assert "Promoted" in msg
        assert manager.rollouts["pkg-ota-99"].phase == "promoted"


def test_autonomous_rollback_on_thermal_throttle():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = FleetManager(storage_dir=tmpdir)

        n1 = FleetNodeProfile("node-canary", "pi5", "Raspberry Pi 5", "BCM2712", 8192, 4096, 50.0, 0, "smollm2-135m", "1.0.0")
        manager.enroll_node(n1)

        pkg = OTAPackage("pkg-heavy", "llama-3.2-3b", "q8_0", "3.0.0", "heavy123", rollout_strategy="canary", canary_ratio=1.0)
        manager.create_ota_deployment(pkg)

        # Simulate thermal throttling on canary node
        manager.record_heartbeat("node-canary", {"cpu_temp_c": 86.5, "thermal_state": 1})
        assert manager.nodes["node-canary"].status == "throttled"

        # Evaluate canary -> MUST trigger autonomous rollback!
        success, msg = manager.evaluate_canary("pkg-heavy")
        assert success is False
        assert "Rollback triggered" in msg
        assert manager.rollouts["pkg-heavy"].phase == "rolled_back"
        assert manager.nodes["node-canary"].current_model == "stable-fallback-model"


def test_cli_fleet_commands():
    runner = CliRunner()

    # Status
    res_status = runner.invoke(cli, ["fleet", "status"])
    assert res_status.exit_code == 0
    assert "Cluster Edge Nodes" in res_status.output

    # Status JSON
    res_json = runner.invoke(cli, ["fleet", "status", "--json"])
    assert res_json.exit_code == 0
    assert "summary" in res_json.output

    # Enroll
    res_enroll = runner.invoke(cli, ["fleet", "enroll", "--node-id", "test-node-99"])
    assert res_enroll.exit_code == 0
    assert "test-node-99" in res_enroll.output

    # Deploy
    res_deploy = runner.invoke(cli, ["fleet", "deploy", "smollm2-135m", "--strategy", "canary"])
    assert res_deploy.exit_code == 0
    assert "Created signed OTA Deployment" in res_deploy.output

    # Rollback
    res_rb = runner.invoke(cli, ["fleet", "rollback"])
    assert res_rb.exit_code == 0
    assert "Reverted models" in res_rb.output
