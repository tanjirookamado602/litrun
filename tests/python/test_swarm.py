"""
Unit tests for litrun Edge Swarm and Decentralized Mesh Protocol
"""

import time
from click.testing import CliRunner
from litrun.cli.main import cli
from litrun.swarm import SwarmNode, SwarmMesh, SwarmRouter


def test_swarm_node_create_local():
    node = SwarmNode.create_local(port=8080)
    assert len(node.node_id) > 0
    assert node.ram_total_mb > 0
    assert node.ram_avail_mb >= 0
    assert node.port == 8080

    d = node.to_dict()
    node2 = SwarmNode.from_dict(d)
    assert node.node_id == node2.node_id
    assert node.hostname == node2.hostname


def test_swarm_mesh_lifecycle():
    local_node = SwarmNode.create_local()
    mesh = SwarmMesh(local_node=local_node)

    # Add mock remote peer node
    peer = SwarmNode(
        node_id="peer001",
        hostname="rpi5-node",
        ip="192.168.1.150",
        port=8080,
        board_name="Raspberry Pi 5",
        soc="BCM2712",
        cores=4,
        ram_total_mb=8192,
        ram_avail_mb=6200,
        thermal_state=0,
        has_npu=False,
        npu_tops=0.0,
        has_gpu=False,
        vlm_ready=True,
        hear_ready=True,
        last_seen=time.time(),
    )
    mesh.update_peer(peer)
    nodes = mesh.get_all_nodes()
    assert len(nodes) == 2
    assert mesh.get_node("peer001").hostname == "rpi5-node"

    # Test stale pruning
    peer.last_seen = time.time() - 30.0
    removed = mesh.prune_stale(max_age_seconds=15.0)
    assert removed == 1
    assert len(mesh.get_all_nodes()) == 1


def test_swarm_router_capabilities():
    local_node = SwarmNode.create_local()
    mesh = SwarmMesh(local_node=local_node)

    # NPU node
    opi5 = SwarmNode(
        node_id="opi5-npu",
        hostname="orangepi5-ai",
        ip="192.168.1.180",
        port=8080,
        board_name="Orange Pi 5",
        soc="RK3588",
        cores=8,
        ram_total_mb=16384,
        ram_avail_mb=12000,
        thermal_state=0,
        has_npu=True,
        npu_tops=6.0,
        has_gpu=False,
        vlm_ready=True,
        hear_ready=False,
        last_seen=time.time(),
    )
    mesh.update_peer(opi5)

    router = SwarmRouter(mesh)

    # Vision task should select NPU node
    best_vlm, reason_vlm = router.select_best_node(task_type="vision")
    assert best_vlm.node_id == "opi5-npu"
    assert "Vision" in reason_vlm

    # Audio task
    best_audio, reason_audio = router.select_best_node(task_type="audio")
    assert "Audio" in reason_audio

    # Dispatch should succeed
    res = router.dispatch("Read gauge level", task_type="reasoning", timeout_seconds=0.1)
    assert "response" in res
    assert "routing_reason" in res


def test_cli_swarm_status_and_dispatch():
    runner = CliRunner()
    res_status = runner.invoke(cli, ["swarm", "status"])
    assert res_status.exit_code == 0
    assert "Swarm Mesh Status" in res_status.output

    res_json = runner.invoke(cli, ["swarm", "status", "--json"])
    assert res_json.exit_code == 0
    assert '"node_id":' in res_json.output

    res_dispatch = runner.invoke(cli, ["swarm", "dispatch", "-p", "Test dispatch prompt"])
    assert res_dispatch.exit_code == 0
    assert "Dispatching to Edge Swarm" in res_dispatch.output
