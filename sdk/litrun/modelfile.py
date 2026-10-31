"""
litrun Modelfile Specification & Custom Model Packaging Engine
Allows defining custom edge agent models via a declarative Modelfile:
    FROM smollm2-135m
    PARAMETER temperature 0.3
    PARAMETER max_tokens 256
    SYSTEM \"\"\"You are an autonomous edge rover running on Raspberry Pi 5.\"\"\"
    ADAPTER ./adapters/rover.litlora
    LICENSE \"\"\"Apache-2.0\"\"\"
"""

from __future__ import annotations
import os
import re
import json
import time
import shutil
import tarfile
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class ParsedModelfile:
    base_model: str = ""
    system_prompt: Optional[str] = None
    template: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    adapter_path: Optional[str] = None
    license: Optional[str] = None
    messages: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParsedModelfile":
        return cls(
            base_model=data.get("base_model", ""),
            system_prompt=data.get("system_prompt"),
            template=data.get("template"),
            parameters=data.get("parameters", {}),
            adapter_path=data.get("adapter_path"),
            license=data.get("license"),
            messages=data.get("messages", []),
        )


class ModelfileParser:
    """Parses standard edge Modelfiles into structured configuration."""

    @staticmethod
    def parse(content: str, base_dir: Optional[str] = None) -> ParsedModelfile:
        lines = content.splitlines()
        parsed = ParsedModelfile()
        i = 0
        n = len(lines)

        while i < n:
            raw_line = lines[i]
            line = raw_line.strip()
            i += 1

            if not line or line.startswith("#"):
                continue

            parts = line.split(None, 1)
            directive = parts[0].upper()
            val = parts[1].strip() if len(parts) > 1 else ""

            if directive == "FROM":
                parsed.base_model = val.strip("\"'")

            elif directive == "PARAMETER":
                p_parts = val.split(None, 1)
                if len(p_parts) == 2:
                    p_key = p_parts[0].lower()
                    p_raw_val = p_parts[1].strip("\"'")
                    # Type conversion
                    if p_raw_val.lower() in ("true", "false"):
                        p_val = p_raw_val.lower() == "true"
                    else:
                        try:
                            if "." in p_raw_val:
                                p_val = float(p_raw_val)
                            else:
                                p_val = int(p_raw_val)
                        except ValueError:
                            p_val = p_raw_val
                    parsed.parameters[p_key] = p_val

            elif directive in ("SYSTEM", "TEMPLATE", "LICENSE"):
                # Multi-line quote support: """ or '''
                if val.startswith('"""') or val.startswith("'''"):
                    quote_mark = val[:3]
                    content_after = val[3:]
                    if content_after.endswith(quote_mark) and len(content_after) >= 3:
                        text_val = content_after[:-3]
                    else:
                        multi_lines = [content_after]
                        while i < n:
                            next_line = lines[i]
                            i += 1
                            if quote_mark in next_line:
                                end_idx = next_line.index(quote_mark)
                                multi_lines.append(next_line[:end_idx])
                                break
                            else:
                                multi_lines.append(next_line)
                        text_val = "\n".join(multi_lines)
                else:
                    text_val = val.strip("\"'")

                if directive == "SYSTEM":
                    parsed.system_prompt = text_val
                elif directive == "TEMPLATE":
                    parsed.template = text_val
                elif directive == "LICENSE":
                    parsed.license = text_val

            elif directive == "ADAPTER":
                adapter_p = val.strip("\"'")
                if base_dir and not os.path.isabs(adapter_p):
                    adapter_p = os.path.normpath(os.path.join(base_dir, adapter_p))
                parsed.adapter_path = adapter_p

            elif directive == "MESSAGE":
                m_parts = val.split(None, 1)
                if len(m_parts) == 2:
                    parsed.messages.append({"role": m_parts[0].lower(), "content": m_parts[1].strip("\"'")})

        if not parsed.base_model:
            raise ValueError("Modelfile missing mandatory 'FROM <base_model>' directive.")

        return parsed

    @classmethod
    def parse_file(cls, path: str) -> ParsedModelfile:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Modelfile not found at '{path}'")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return cls.parse(content, base_dir=os.path.dirname(os.path.abspath(path)))


@dataclass
class CustomModelManifest:
    tag: str
    created_at: float
    base_model: str
    system_prompt: Optional[str]
    parameters: Dict[str, Any]
    adapter_filename: Optional[str] = None
    template: Optional[str] = None
    license: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CustomModelManifest":
        return cls(
            tag=data["tag"],
            created_at=data.get("created_at", time.time()),
            base_model=data.get("base_model", ""),
            system_prompt=data.get("system_prompt"),
            parameters=data.get("parameters", {}),
            adapter_filename=data.get("adapter_filename"),
            template=data.get("template"),
            license=data.get("license"),
        )


def _sanitize_tag(tag: str) -> str:
    return tag.replace(":", "_").replace("/", "_").replace("\\", "_")


def get_custom_models_root() -> str:
    cache_dir = os.path.expanduser("~/.cache/litrun/custom_models")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def save_custom_model(tag: str, parsed: ParsedModelfile) -> CustomModelManifest:
    """Builds and stores a custom model entry under ~/.cache/litrun/custom_models/<tag>"""
    root = get_custom_models_root()
    sanitized = _sanitize_tag(tag)
    model_dir = os.path.join(root, sanitized)
    os.makedirs(model_dir, exist_ok=True)

    adapter_fname = None
    if parsed.adapter_path:
        if os.path.isfile(parsed.adapter_path):
            adapter_fname = os.path.basename(parsed.adapter_path)
            dest_adapter = os.path.join(model_dir, adapter_fname)
            shutil.copyfile(parsed.adapter_path, dest_adapter)
        else:
            adapter_fname = parsed.adapter_path

    manifest = CustomModelManifest(
        tag=tag,
        created_at=time.time(),
        base_model=parsed.base_model,
        system_prompt=parsed.system_prompt,
        parameters=parsed.parameters,
        adapter_filename=adapter_fname,
        template=parsed.template,
        license=parsed.license,
    )

    manifest_path = os.path.join(model_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest.to_dict(), f, indent=2)

    return manifest


def get_custom_model(tag: str) -> Optional[CustomModelManifest]:
    """Retrieves manifest of a registered custom model."""
    root = get_custom_models_root()
    sanitized = _sanitize_tag(tag)
    manifest_path = os.path.join(root, sanitized, "manifest.json")
    if not os.path.isfile(manifest_path):
        # Also try searching exact match without tag suffix
        if ":" not in tag:
            for d in os.listdir(root):
                if d == f"{tag}_latest" or d.startswith(f"{tag}_"):
                    candidate = os.path.join(root, d, "manifest.json")
                    if os.path.isfile(candidate):
                        manifest_path = candidate
                        break
        if not os.path.isfile(manifest_path):
            return None

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return CustomModelManifest.from_dict(data)
    except Exception:
        return None


def list_custom_models() -> List[CustomModelManifest]:
    """Returns all registered custom models."""
    root = get_custom_models_root()
    models = []
    if not os.path.isdir(root):
        return models

    for entry in sorted(os.listdir(root)):
        mpath = os.path.join(root, entry, "manifest.json")
        if os.path.isfile(mpath):
            try:
                with open(mpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                models.append(CustomModelManifest.from_dict(data))
            except Exception:
                continue
    return models


def delete_custom_model(tag: str) -> bool:
    """Removes a custom model from the local repository."""
    root = get_custom_models_root()
    sanitized = _sanitize_tag(tag)
    model_dir = os.path.join(root, sanitized)
    if os.path.isdir(model_dir):
        shutil.rmtree(model_dir)
        return True
    return False


def export_custom_model_pack(tag: str, output_path: str) -> str:
    """Packages a custom model into a distributable .litpack gzip archive."""
    root = get_custom_models_root()
    sanitized = _sanitize_tag(tag)
    model_dir = os.path.join(root, sanitized)
    if not os.path.isdir(model_dir):
        raise ValueError(f"Custom model '{tag}' does not exist.")

    if not output_path.endswith(".litpack") and not output_path.endswith(".tar.gz"):
        output_path = f"{output_path}.litpack"

    with tarfile.open(output_path, "w:gz") as tar:
        for fname in os.listdir(model_dir):
            fpath = os.path.join(model_dir, fname)
            tar.add(fpath, arcname=fname)

    return os.path.abspath(output_path)


def import_custom_model_pack(pack_path: str, tag: Optional[str] = None) -> CustomModelManifest:
    """Imports a .litpack archive into the local custom model registry."""
    if not os.path.isfile(pack_path):
        raise FileNotFoundError(f"Bundle file not found: {pack_path}")

    root = get_custom_models_root()
    temp_dir = os.path.join(root, f"_import_tmp_{int(time.time()*1000)}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        with tarfile.open(pack_path, "r:gz") as tar:
            tar.extractall(temp_dir)

        manifest_path = os.path.join(temp_dir, "manifest.json")
        if not os.path.isfile(manifest_path):
            raise ValueError("Invalid .litpack package: missing manifest.json")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        final_tag = tag or manifest_data.get("tag", "imported-model:latest")
        manifest_data["tag"] = final_tag
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        dest_dir = os.path.join(root, _sanitize_tag(final_tag))
        if os.path.isdir(dest_dir):
            shutil.rmtree(dest_dir)
        shutil.move(temp_dir, dest_dir)

        return CustomModelManifest.from_dict(manifest_data)
    finally:
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
