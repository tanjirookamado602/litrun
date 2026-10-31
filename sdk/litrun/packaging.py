"""
litrun Native Debian Packaging Subsystem
Pure-Python zero-dependency Debian (.deb) package generator.
Builds litrun_<version>_<arch>.deb for Raspberry Pi OS, Debian, and Ubuntu.
"""

from __future__ import annotations
import io
import os
import sys
import tarfile
import time


def make_ar_header(filename: str, size: int, mode: int = 0o100644, mtime: int = 0) -> bytes:
    """Format 60-byte standard UNIX ar header."""
    fn = (filename + "/").ljust(16)[:16]
    mt = str(mtime).ljust(12)[:12]
    uid = "0".ljust(6)[:6]
    gid = "0".ljust(6)[:6]
    md = oct(mode)[2:].rjust(6, "0") + "  "
    sz = str(size).ljust(10)[:10]
    magic = b"`\n"
    return f"{fn}{mt}{uid}{gid}{md}{sz}".encode("ascii") + magic


def create_control_archive(version: str, arch: str) -> bytes:
    """Create control.tar.gz in memory."""
    control_content = f"""Package: litrun
Version: {version}
Section: utils
Priority: optional
Architecture: {arch}
Maintainer: assassinaj602 <assassinaj602@github.com>
Homepage: https://github.com/assassinaj602/litrun
Description: Universal Lightweight Embedded Linux AI Runtime
 High-performance edge AI inference runtime for Raspberry Pi, Orange Pi,
 Jetson, and x86 single-board computers with hardware governor and zero cloud latency.
"""
    postinst_content = """#!/bin/sh
set -e
if command -v systemctl >/dev/null 2>&1; then
    systemctl daemon-reload || true
fi
exit 0
"""
    prerm_content = """#!/bin/sh
set -e
if command -v systemctl >/dev/null 2>&1; then
    systemctl stop litrun.service >/dev/null 2>&1 || true
    systemctl disable litrun.service >/dev/null 2>&1 || true
fi
exit 0
"""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        ctrl_bytes = control_content.encode("utf-8")
        ti = tarfile.TarInfo("./control")
        ti.size = len(ctrl_bytes)
        ti.mode = 0o644
        ti.mtime = int(time.time())
        tar.addfile(ti, io.BytesIO(ctrl_bytes))

        post_bytes = postinst_content.encode("utf-8")
        ti = tarfile.TarInfo("./postinst")
        ti.size = len(post_bytes)
        ti.mode = 0o755
        ti.mtime = int(time.time())
        tar.addfile(ti, io.BytesIO(post_bytes))

        prerm_bytes = prerm_content.encode("utf-8")
        ti = tarfile.TarInfo("./prerm")
        ti.size = len(prerm_bytes)
        ti.mode = 0o755
        ti.mtime = int(time.time())
        tar.addfile(ti, io.BytesIO(prerm_bytes))

    return buf.getvalue()


def create_data_archive(repo_root: str, arch: str) -> bytes:
    """Create data.tar.gz containing filesystem hierarchy."""
    buf = io.BytesIO()
    now = int(time.time())

    service_content = """[Unit]
Description=litrun Edge AI Runtime Server
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/litrun serve --host 0.0.0.0 --port 8080
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
"""
    conf_content = """# /etc/litrun/litrun.conf
LITRUN_HOST="0.0.0.0"
LITRUN_PORT=8080
LITRUN_MAX_RAM_PERCENT=80
LITRUN_SWARM_PORT=50505
"""
    launcher_content = """#!/usr/bin/env python3
import sys
from litrun.cli.main import cli
if __name__ == "__main__":
    sys.exit(cli())
"""

    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        conf_bytes = conf_content.encode("utf-8")
        ti = tarfile.TarInfo("./etc/litrun/litrun.conf")
        ti.size = len(conf_bytes)
        ti.mode = 0o644
        ti.mtime = now
        tar.addfile(ti, io.BytesIO(conf_bytes))

        svc_bytes = service_content.encode("utf-8")
        ti = tarfile.TarInfo("./lib/systemd/system/litrun.service")
        ti.size = len(svc_bytes)
        ti.mode = 0o644
        ti.mtime = now
        tar.addfile(ti, io.BytesIO(svc_bytes))

        launch_bytes = launcher_content.encode("utf-8")
        ti = tarfile.TarInfo("./usr/bin/litrun")
        ti.size = len(launch_bytes)
        ti.mode = 0o755
        ti.mtime = now
        tar.addfile(ti, io.BytesIO(launch_bytes))

        lib_path = os.path.join(repo_root, "core", "lib", "liblitrun_core.so")
        if os.path.exists(lib_path):
            with open(lib_path, "rb") as f:
                lib_data = f.read()
            ti = tarfile.TarInfo("./usr/lib/litrun/liblitrun_core.so")
            ti.size = len(lib_data)
            ti.mode = 0o755
            ti.mtime = now
            tar.addfile(ti, io.BytesIO(lib_data))

        probe_path = os.path.join(repo_root, "core", "bin", "litrun-probe")
        if os.path.exists(probe_path):
            with open(probe_path, "rb") as f:
                probe_data = f.read()
            ti = tarfile.TarInfo("./usr/bin/litrun-probe")
            ti.size = len(probe_data)
            ti.mode = 0o755
            ti.mtime = now
            tar.addfile(ti, io.BytesIO(probe_data))

        sdk_litrun = os.path.join(repo_root, "sdk", "litrun")
        for root, dirs, files in os.walk(sdk_litrun):
            if "__pycache__" in root:
                continue
            rel_dir = os.path.relpath(root, sdk_litrun)
            for f in files:
                if f.endswith((".pyc", ".pyo")):
                    continue
                file_full = os.path.join(root, f)
                target_path = os.path.normpath(
                    os.path.join("./usr/lib/python3/dist-packages/litrun", rel_dir, f)
                )
                with open(file_full, "rb") as f_obj:
                    content = f_obj.read()
                ti = tarfile.TarInfo(target_path)
                ti.size = len(content)
                ti.mode = 0o644
                ti.mtime = now
                tar.addfile(ti, io.BytesIO(content))

    return buf.getvalue()


def build_deb_package(output_path: str, version: str, arch: str, repo_root: str) -> None:
    """Combines debian-binary, control.tar.gz, and data.tar.gz into standard ar .deb file."""
    debian_binary = b"2.0\n"
    control_gz = create_control_archive(version, arch)
    data_gz = create_data_archive(repo_root, arch)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with open(output_path, "wb") as deb:
        deb.write(b"!<arch>\n")

        deb.write(make_ar_header("debian-binary", len(debian_binary)))
        deb.write(debian_binary)
        if len(debian_binary) % 2 != 0:
            deb.write(b"\n")

        deb.write(make_ar_header("control.tar.gz", len(control_gz)))
        deb.write(control_gz)
        if len(control_gz) % 2 != 0:
            deb.write(b"\n")

        deb.write(make_ar_header("data.tar.gz", len(data_gz)))
        deb.write(data_gz)
        if len(data_gz) % 2 != 0:
            deb.write(b"\n")
