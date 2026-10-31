#!/usr/bin/env python3
"""
litrun Test Runner
Executes all unit tests in tests/python/ with detailed pass/fail reporting.
"""

import os
import sys
import time
import inspect
import importlib

# Ensure sdk and repo root are in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sdk")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

TEST_MODULES = [
    "tests.python.test_hardware",
    "tests.python.test_governor",
    "tests.python.test_registry",
    "tests.python.test_session",
    "tests.python.test_grammar",
    "tests.python.test_model",
    "tests.python.test_cli",
    "tests.python.test_server",
    "tests.python.test_see",
    "tests.python.test_vision",
    "tests.python.test_tools",
    "tests.python.test_hear",
    "tests.python.test_ros2",
    "tests.python.test_rknn",
    "tests.python.test_jetson",
    "tests.python.test_rag",
    "tests.python.test_mqtt",
    "tests.python.test_benchmark",
    "tests.python.test_engine_ffi",
    "tests.python.test_swarm",
    "tests.python.test_lora",
    "tests.python.test_deb_packaging",
    "tests.python.test_modelfile",
    "tests.python.test_quantize",
    "tests.python.test_fleet",
]


def main():
    print("=" * 60)
    print("⚡ litrun Python Test Suite Runner")
    print("=" * 60)

    total_passed = 0
    total_failed = 0
    start_time = time.perf_counter()

    for mod_name in TEST_MODULES:
        print(f"\n[SUITE] {mod_name}")
        try:
            mod = importlib.import_module(mod_name)
        except Exception as e:
            print(f"  ✗ Failed to import {mod_name}: {e}")
            total_failed += 1
            continue

        test_funcs = [
            (name, func)
            for name, func in inspect.getmembers(mod, inspect.isfunction)
            if name.startswith("test_")
        ]

        for name, func in test_funcs:
            t0 = time.perf_counter()
            try:
                func()
                elapsed = (time.perf_counter() - t0) * 1000.0
                print(f"  ✓ {name} ({elapsed:.1f}ms)")
                total_passed += 1
            except Exception as e:
                elapsed = (time.perf_counter() - t0) * 1000.0
                print(f"  ✗ {name} FAILED ({elapsed:.1f}ms): {e}")
                import traceback
                traceback.print_exc()
                total_failed += 1

    total_elapsed = time.perf_counter() - start_time
    print("\n" + "=" * 60)
    print(f"Test Summary: {total_passed} passed, {total_failed} failed in {total_elapsed:.2f}s")
    print("=" * 60)

    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
