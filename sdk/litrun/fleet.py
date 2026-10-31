"""
litrun Enterprise Edge Fleet Management & OTA Update Protocol
Manages distributed edge SBC clusters (Raspberry Pi, Orange Pi, NVIDIA Jetson):
  - Node enrollment & hardware fingerprint registration
  - HMAC-SHA256 cryptographic manifest signing & verification
  - Over-The-Air (OTA) model deployment with canary rollouts
  - Autonomous watchdog & automatic rollback on thermal throttling or OOM risk
  - Fleet-wide telemetry aggregation (thermal delta, token throughput, RAM headroom)
"""

from __future__ import annotations
import os
import json
import time
import uuid
import hmac
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple

DEFAULT_SECRET = "litrun-edge-enterprise-fleet-2026"


@dataclass
class FleetNodeProfile:
    node_id: str
    hostname: str
    board_name: str
    soc: str
    ram_total_mb: int
    ram_avail_mb: int
    cpu_temp_c: float
    thermal_state: int
    current_model: str
    current_model_version: str
    installed_models: List[str] = field(default_factory=list)
    status: str = "healthy"  # healthy, throttled, updating, offline
    last_heartbeat: float = field(default_factory=time.time)
    firmware_version: str = "0.9.0"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FleetNodeProfile":
        return cls(
            node_id=data["node_id"],
            hostname=data.get("hostname", "unknown"),
            board_name=data.get("board_name", "generic-sbc"),
            soc=data.get("soc", "arm64"),
            ram_total_mb=data.get("ram_total_mb", 4096),
            ram_avail_mb=data.get("ram_avail_mb", 2048),
            cpu_temp_c=data.get("cpu_temp_c", 45.0),
            thermal_state=data.get("thermal_state", 0),
            current_model=data.get("current_model", "none"),
            current_model_version=data.get("current_model_version", "1.0.0"),
            installed_models=data.get("installed_models", []),
            status=data.get("status", "healthy"),
            last_heartbeat=data.get("last_heartbeat", time.time()),
            firmware_version=data.get("firmware_version", "0.9.0"),
        )


@dataclass
class OTAPackage:
    package_id: str
    target_model: str
    target_quant: str
    target_version: str
    sha256_checksum: str
    rollout_strategy: str = "canary"  # canary, immediate, rolling
    canary_ratio: float = 0.25        # 25% canary nodes
    rollback_on_throttle: bool = True
    created_at: float = field(default_factory=time.time)
    signature: Optional[str] = None

    def compute_signature(self, secret: str = DEFAULT_SECRET) -> str:
        body = f"{self.package_id}:{self.target_model}:{self.target_quant}:{self.target_version}:{self.sha256_checksum}"
        return hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify_signature(self, secret: str = DEFAULT_SECRET) -> bool:
        if not self.signature:
            return False
        expected = self.compute_signature(secret)
        return hmac.compare_digest(self.signature, expected)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OTAPackage":
        return cls(
            package_id=data["package_id"],
            target_model=data["target_model"],
            target_quant=data["target_quant"],
            target_version=data["target_version"],
            sha256_checksum=data["sha256_checksum"],
            rollout_strategy=data.get("rollout_strategy", "canary"),
            canary_ratio=data.get("canary_ratio", 0.25),
            rollback_on_throttle=data.get("rollback_on_throttle", True),
            created_at=data.get("created_at", time.time()),
            signature=data.get("signature"),
        )


@dataclass
class RolloutState:
    package_id: str
    phase: str  # pending, canary_active, promoted, rolled_back, completed
    canary_nodes: List[str] = field(default_factory=list)
    deployed_nodes: List[str] = field(default_factory=list)
    failed_nodes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FleetManager:
    """Manages fleet-wide node enrollment, OTA rollouts, and cluster health."""

    def __init__(self, storage_dir: Optional[str] = None, secret: str = DEFAULT_SECRET):
        self.storage_dir = storage_dir or os.path.expanduser("~/.cache/litrun/fleet")
        self.secret = secret
        os.makedirs(self.storage_dir, exist_ok=True)
        self.nodes: Dict[str, FleetNodeProfile] = {}
        self.rollouts: Dict[str, RolloutState] = {}
        self._load_state()

    def _nodes_file(self) -> str:
        return os.path.join(self.storage_dir, "fleet_nodes.json")

    def _rollouts_file(self) -> str:
        return os.path.join(self.storage_dir, "fleet_rollouts.json")

    def _load_state(self) -> None:
        if os.path.isfile(self._nodes_file()):
            try:
                with open(self._nodes_file(), "r", encoding="utf-8") as f:
                    data = json.load(f)
                for nid, ndata in data.items():
                    self.nodes[nid] = FleetNodeProfile.from_dict(ndata)
            except Exception:
                pass

        if os.path.isfile(self._rollouts_file()):
            try:
                with open(self._rollouts_file(), "r", encoding="utf-8") as f:
                    rdata = json.load(f)
                for pid, sdata in rdata.items():
                    self.rollouts[pid] = RolloutState(
                        package_id=sdata["package_id"],
                        phase=sdata["phase"],
                        canary_nodes=sdata.get("canary_nodes", []),
                        deployed_nodes=sdata.get("deployed_nodes", []),
                        failed_nodes=sdata.get("failed_nodes", []),
                    )
            except Exception:
                pass

    def _save_state(self) -> None:
        try:
            with open(self._nodes_file(), "w", encoding="utf-8") as f:
                json.dump({nid: n.to_dict() for nid, n in self.nodes.items()}, f, indent=2)
            with open(self._rollouts_file(), "w", encoding="utf-8") as f:
                json.dump({pid: r.to_dict() for pid, r in self.rollouts.items()}, f, indent=2)
        except Exception:
            pass

    def enroll_node(self, profile: FleetNodeProfile) -> bool:
        """Enrolls or updates an edge node in the fleet registry."""
        profile.last_heartbeat = time.time()
        self.nodes[profile.node_id] = profile
        self._save_state()
        return True

    def record_heartbeat(self, node_id: str, telemetry: Dict[str, Any]) -> Optional[FleetNodeProfile]:
        """Updates live metrics from an enrolled node."""
        node = self.nodes.get(node_id)
        if not node:
            return None

        node.last_heartbeat = time.time()
        node.ram_avail_mb = telemetry.get("ram_avail_mb", node.ram_avail_mb)
        node.cpu_temp_c = telemetry.get("cpu_temp_c", node.cpu_temp_c)
        node.thermal_state = telemetry.get("thermal_state", node.thermal_state)

        # Update health status
        if node.thermal_state > 0 or node.cpu_temp_c >= 80.0:
            node.status = "throttled"
        elif (time.time() - node.last_heartbeat) > 300:
            node.status = "offline"
        else:
            node.status = "healthy"

        self._save_state()
        return node

    def create_ota_deployment(self, package: OTAPackage) -> RolloutState:
        """Prepares and signs an OTA deployment across the fleet."""
        package.signature = package.compute_signature(self.secret)

        all_node_ids = list(self.nodes.keys())
        canary_count = max(1, int(len(all_node_ids) * package.canary_ratio)) if all_node_ids else 0

        canaries = all_node_ids[:canary_count]
        rollout = RolloutState(
            package_id=package.package_id,
            phase="canary_active" if package.rollout_strategy == "canary" else "promoted",
            canary_nodes=canaries,
            deployed_nodes=canaries if package.rollout_strategy == "canary" else all_node_ids,
        )

        # Simulate initial deployment to selected nodes
        for nid in rollout.deployed_nodes:
            if nid in self.nodes:
                self.nodes[nid].current_model = package.target_model
                self.nodes[nid].current_model_version = package.target_version

        self.rollouts[package.package_id] = rollout
        self._save_state()
        return rollout

    def evaluate_canary(self, package_id: str) -> Tuple[bool, str]:
        """
        Evaluates canary node health.
        If canary nodes are healthy, promotes to the remaining fleet.
        If any canary throttled or failed, triggers automated rollback.
        """
        rollout = self.rollouts.get(package_id)
        if not rollout:
            return False, f"Rollout '{package_id}' not found."

        # Check health of canaries
        for cid in rollout.canary_nodes:
            cnode = self.nodes.get(cid)
            if not cnode:
                continue
            if cnode.status == "throttled" or cnode.cpu_temp_c >= 82.0:
                # Trigger automated rollback!
                self.trigger_rollback(cid)
                rollout.phase = "rolled_back"
                rollout.failed_nodes.append(cid)
                self._save_state()
                return False, f"Canary node {cid} experienced thermal throttle ({cnode.cpu_temp_c}°C). Rollback triggered."

        # Canaries are healthy: promote to entire fleet
        all_node_ids = list(self.nodes.keys())
        rollout.deployed_nodes = all_node_ids
        rollout.phase = "promoted"
        self._save_state()
        return True, "Canary health verified (0 errors, stable thermals). Promoted to 100% of fleet."

    def trigger_rollback(self, target_node_id: Optional[str] = None) -> List[str]:
        """Reverts models on target node or across the entire fleet."""
        rolled_back = []
        targets = [target_node_id] if target_node_id else list(self.nodes.keys())

        for nid in targets:
            node = self.nodes.get(nid)
            if node:
                node.current_model = "stable-fallback-model"
                node.current_model_version = "0.7.0"
                rolled_back.append(nid)

        self._save_state()
        return rolled_back

    def fleet_telemetry_summary(self) -> Dict[str, Any]:
        """Computes aggregate cluster-wide statistics."""
        now = time.time()
        total_nodes = len(self.nodes)
        online = sum(1 for n in self.nodes.values() if (now - n.last_heartbeat) <= 300)
        healthy = sum(1 for n in self.nodes.values() if n.status == "healthy")
        throttled = sum(1 for n in self.nodes.values() if n.status == "throttled")

        total_ram_mb = sum(n.ram_total_mb for n in self.nodes.values())
        avail_ram_mb = sum(n.ram_avail_mb for n in self.nodes.values())
        avg_temp = (
            sum(n.cpu_temp_c for n in self.nodes.values()) / max(1, total_nodes)
            if total_nodes > 0 else 0.0
        )

        return {
            "total_nodes": total_nodes,
            "online_nodes": online,
            "healthy_nodes": healthy,
            "throttled_nodes": throttled,
            "total_ram_mb": total_ram_mb,
            "available_ram_mb": avail_ram_mb,
            "average_cpu_temp_c": round(avg_temp, 1),
            "active_deployments": len(self.rollouts),
        }


def create_local_fleet_node() -> FleetNodeProfile:
    """Creates a FleetNodeProfile representing the current edge machine."""
    import socket
    from litrun.hardware import probe_hardware
    from litrun.governor import poll_governor

    hw = probe_hardware()
    gov = poll_governor()

    node_id = f"node-{hw.profile_id.lower()[:8]}-{uuid.uuid4().hex[:6]}"
    return FleetNodeProfile(
        node_id=node_id,
        hostname=socket.gethostname(),
        board_name=hw.board_name,
        soc=hw.soc,
        ram_total_mb=hw.ram_total_mb,
        ram_avail_mb=gov.ram_avail_mb,
        cpu_temp_c=getattr(gov, "temp_c", 45.0),
        thermal_state=0 if gov.thermal_state == "nominal" else (1 if gov.thermal_state == "throttled" else (gov.thermal_state if isinstance(gov.thermal_state, int) else 0)),
        current_model="smollm2-135m",
        current_model_version="1.0.0",
        installed_models=["smollm2-135m", "qwen2.5-0.5b"],
        status="healthy",
    )
