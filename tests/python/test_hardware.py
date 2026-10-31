from litrun.hardware import probe_hardware, HardwareProfile, _pure_python_probe


def test_probe_hardware():
    hw = probe_hardware()
    assert isinstance(hw, HardwareProfile)
    assert len(hw.arch) > 0
    assert len(hw.board_name) > 0
    assert len(hw.soc) > 0
    assert len(hw.profile_id) > 0
    assert hw.cores > 0
    assert hw.ram_total_mb > 0
    assert hw.ram_avail_mb >= 0


def test_pure_python_probe_fallback():
    hw = _pure_python_probe()
    assert isinstance(hw, HardwareProfile)
    assert hw.cores > 0
    assert hw.ram_total_mb > 0
    assert len(hw.profile_id) > 0


def test_hardware_to_dict():
    hw = probe_hardware()
    d = hw.to_dict()
    assert isinstance(d, dict)
    assert "profile_id" in d
    assert "ram_total_mb" in d
    assert "has_neon" in d
    assert "has_rvv" in d


def test_riscv_fixture_hardware_detection():
    import os
    orig = os.environ.get("LITRUN_SYSROOT")
    try:
        os.environ["LITRUN_SYSROOT"] = "tests/fixtures/milkv_pioneer"
        hw = probe_hardware()
        assert hw.arch == "riscv64"
        assert hw.soc == "SG2042"
        assert hw.has_rvv is True
        assert "riscv64" in hw.profile_id
    finally:
        if orig:
            os.environ["LITRUN_SYSROOT"] = orig
        else:
            os.environ.pop("LITRUN_SYSROOT", None)
