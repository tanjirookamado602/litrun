"""
litrun On-Device LoRA Adaptation Engine
Pure-Python, zero-dependency Low-Rank Adaptation (LoRA) for edge fine-tuning.
Enables fine-tuning SmolLM2 and edge LLM adapters directly on Raspberry Pi / Jetson.
"""

from __future__ import annotations
import dataclasses
import json
import math
import os
import random
import time
from typing import Dict, List, Optional, Tuple


@dataclasses.dataclass
class LoRAConfig:
    adapter_name: str
    base_model: str = "smollm2-135m"
    rank: int = 4
    alpha: float = 8.0
    in_dim: int = 576       # Default hidden dimension for SmolLM2-135M
    out_dim: int = 576
    target_modules: List[str] = dataclasses.field(default_factory=lambda: ["q_proj", "v_proj"])
    created_at: float = dataclasses.field(default_factory=time.time)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LoRAConfig":
        return cls(**data)


class LoRALayer:
    """
    Low-rank adaptation layer: delta_W = (alpha / rank) * (B @ A)
    A: (rank x in_dim) initialized ~ N(0, 0.02)
    B: (out_dim x rank) initialized to 0.0
    """

    def __init__(self, in_dim: int, out_dim: int, rank: int, alpha: float):
        self.in_dim = in_dim
        self.out_dim = out_dim
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / max(1, rank)

        # Initialize A with small Gaussian noise
        # A is rank x in_dim (rows=rank, cols=in_dim)
        self.A: List[List[float]] = [
            [random.gauss(0.0, 0.02) for _ in range(in_dim)]
            for _ in range(rank)
        ]
        # Initialize B with zeros
        # B is out_dim x rank (rows=out_dim, cols=rank)
        self.B: List[List[float]] = [
            [0.0 for _ in range(rank)]
            for _ in range(out_dim)
        ]

    def forward(self, x: List[float]) -> List[float]:
        """
        Computes forward pass: delta = scaling * (B @ (A @ x))
        x: vector of length in_dim
        returns: vector of length out_dim
        """
        # Intermediate: h = A @ x (length rank)
        h = [0.0] * self.rank
        for r in range(self.rank):
            row_A = self.A[r]
            dot = 0.0
            for i in range(min(len(x), self.in_dim)):
                dot += row_A[i] * x[i]
            h[r] = dot

        # Output: y = scaling * (B @ h) (length out_dim)
        y = [0.0] * self.out_dim
        for d in range(self.out_dim):
            row_B = self.B[d]
            dot = 0.0
            for r in range(self.rank):
                dot += row_B[r] * h[r]
            y[d] = dot * self.scaling
        return y

    def train_step(self, x: List[float], target: List[float], lr: float = 0.001) -> float:
        """
        Performs one gradient descent step minimizing MSE loss = 0.5 * sum((y - target)^2).
        Returns the scalar MSE loss.
        """
        # Forward pass
        h = [0.0] * self.rank
        for r in range(self.rank):
            row_A = self.A[r]
            dot = sum(row_A[i] * x[i] for i in range(min(len(x), self.in_dim)))
            h[r] = dot

        y = [0.0] * self.out_dim
        for d in range(self.out_dim):
            y[d] = sum(self.B[d][r] * h[r] for r in range(self.rank)) * self.scaling

        # Compute error & loss
        loss = 0.0
        grad_out = [0.0] * self.out_dim
        for d in range(min(len(target), self.out_dim)):
            diff = y[d] - target[d]
            loss += 0.5 * (diff ** 2)
            grad_out[d] = diff * self.scaling

        # Backpropagation:
        # grad_B[d][r] = grad_out[d] * h[r]
        # grad_h[r] = sum_d(grad_out[d] * B[d][r])
        # grad_A[r][i] = grad_h[r] * x[i]
        grad_h = [0.0] * self.rank
        for r in range(self.rank):
            grad_h[r] = sum(grad_out[d] * self.B[d][r] for d in range(self.out_dim))

        # Update B
        for d in range(self.out_dim):
            g_d = grad_out[d]
            for r in range(self.rank):
                self.B[d][r] -= lr * g_d * h[r]

        # Update A
        for r in range(self.rank):
            gh = grad_h[r]
            for i in range(min(len(x), self.in_dim)):
                self.A[r][i] -= lr * gh * x[i]

        return loss / max(1, self.out_dim)


class LoRAAdapter:
    """Full LoRA Adapter consisting of target projection modules and metadata."""

    def __init__(self, config: LoRAConfig):
        self.config = config
        self.layers: Dict[str, LoRALayer] = {}
        for mod in config.target_modules:
            self.layers[mod] = LoRALayer(
                in_dim=config.in_dim,
                out_dim=config.out_dim,
                rank=config.rank,
                alpha=config.alpha,
            )

    @classmethod
    def create(
        cls,
        name: str,
        base_model: str = "smollm2-135m",
        rank: int = 4,
        alpha: float = 8.0,
    ) -> "LoRAAdapter":
        in_dim = 896 if "0.5b" in base_model else 576
        config = LoRAConfig(
            adapter_name=name,
            base_model=base_model,
            rank=rank,
            alpha=alpha,
            in_dim=in_dim,
            out_dim=in_dim,
        )
        return cls(config)

    def train_on_examples(
        self,
        examples: List[Tuple[str, str]],
        epochs: int = 3,
        lr: float = 0.005,
    ) -> dict:
        """
        Fine-tunes the adapter on input/output text examples using embedded pseudo-feature hashing.
        """
        from litrun.rag import compute_lightweight_embedding

        # Embed examples into fixed vectors of size in_dim
        dim = self.config.in_dim
        training_data = []
        for prompt, target_text in examples:
            v_in = compute_lightweight_embedding(prompt, dim=dim)
            v_out = compute_lightweight_embedding(target_text, dim=dim)
            training_data.append((v_in, v_out))

        epoch_losses = []
        start_time = time.time()

        for epoch in range(epochs):
            total_loss = 0.0
            for x, y in training_data:
                for layer in self.layers.values():
                    loss = layer.train_step(x, y, lr=lr)
                    total_loss += loss
            avg_loss = total_loss / (len(training_data) * len(self.layers))
            epoch_losses.append(round(avg_loss, 6))

        elapsed = time.time() - start_time
        return {
            "epochs": epochs,
            "final_loss": epoch_losses[-1] if epoch_losses else 0.0,
            "epoch_losses": epoch_losses,
            "training_time_sec": round(elapsed, 4),
            "examples_count": len(examples),
        }

    def save(self, file_path: str) -> None:
        """Saves adapter parameters and weights to .litlora JSON file."""
        data = {
            "format": "litrun_lora_v1",
            "config": self.config.to_dict(),
            "layers": {
                name: {
                    "A": layer.A,
                    "B": layer.B,
                    "in_dim": layer.in_dim,
                    "out_dim": layer.out_dim,
                    "rank": layer.rank,
                    "alpha": layer.alpha,
                }
                for name, layer in self.layers.items()
            },
        }
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, file_path: str) -> "LoRAAdapter":
        """Loads adapter from .litlora file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        config = LoRAConfig.from_dict(data["config"])
        adapter = cls(config)
        for name, layer_data in data.get("layers", {}).items():
            layer = LoRALayer(
                in_dim=layer_data["in_dim"],
                out_dim=layer_data["out_dim"],
                rank=layer_data["rank"],
                alpha=layer_data["alpha"],
            )
            layer.A = layer_data["A"]
            layer.B = layer_data["B"]
            adapter.layers[name] = layer
        return adapter

    def get_summary(self) -> dict:
        total_params = 0
        for layer in self.layers.values():
            total_params += (layer.in_dim * layer.rank) + (layer.out_dim * layer.rank)

        # 4 bytes per float32
        footprint_kb = round((total_params * 4) / 1024, 2)
        return {
            "name": self.config.adapter_name,
            "base_model": self.config.base_model,
            "rank": self.config.rank,
            "alpha": self.config.alpha,
            "target_modules": self.config.target_modules,
            "trainable_parameters": total_params,
            "memory_footprint_kb": footprint_kb,
        }
