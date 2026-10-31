"""
Unit tests for litrun pure-Python Debian packaging
"""

import os
import tarfile
import tempfile
from litrun.packaging import (
    make_ar_header,
    create_control_archive,
    create_data_archive,
    build_deb_package,
)


def test_ar_header_format():
    header = make_ar_header("debian-binary", 4)
    assert len(header) == 60
    assert header.startswith(b"debian-binary/")
    assert header.endswith(b"`\n")


def test_control_archive_generation():
    ctrl_gz = create_control_archive(version="0.8.0", arch="arm64")
    assert len(ctrl_gz) > 0

    import io
    with tarfile.open(fileobj=io.BytesIO(ctrl_gz), mode="r:gz") as tar:
        names = tar.getnames()
        assert "./control" in names
        assert "./postinst" in names
        assert "./prerm" in names


def test_build_deb_package_file():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    with tempfile.NamedTemporaryFile(suffix=".deb", delete=False) as tmp:
        deb_path = tmp.name

    try:
        build_deb_package(
            output_path=deb_path,
            version="0.8.0",
            arch="arm64",
            repo_root=repo_root,
        )
        assert os.path.isfile(deb_path)
        assert os.path.getsize(deb_path) > 1000

        with open(deb_path, "rb") as f:
            magic = f.read(8)
            assert magic == b"!<arch>\n"
    finally:
        if os.path.exists(deb_path):
            os.remove(deb_path)
