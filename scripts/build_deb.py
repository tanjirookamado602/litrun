#!/usr/bin/env python3
"""
scripts/build_deb.py
CLI wrapper for litrun native Debian packaging.
"""

import os
import sys

# Ensure sdk is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sdk")))

from litrun.packaging import build_deb_package


def _get_version(repo_root: str) -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
    pyproject = os.path.join(repo_root, "pyproject.toml")
    if os.path.exists(pyproject):
        with open(pyproject, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("version ="):
                    return line.split("=")[1].strip().strip('"').strip("'")
    return "0.9.0"


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    version = _get_version(repo_root)
    import platform
    m = platform.machine().lower()
    arch = "arm64" if "aarch64" in m or "arm64" in m else ("amd64" if "x86_64" in m else "armhf")
    if len(sys.argv) > 2:
        arch = sys.argv[2]

    out_deb = os.path.join(repo_root, "dist", f"litrun_{version}_{arch}.deb")
    print(f"📦 Building Debian package: {out_deb}")
    build_deb_package(out_deb, version=version, arch=arch, repo_root=repo_root)
    size_kb = round(os.path.getsize(out_deb) / 1024, 2)
    print(f"✓ Package created successfully ({size_kb} KB)")


if __name__ == "__main__":
    main()
