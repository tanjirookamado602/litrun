"""
Unit tests for litrun in-process C FFI engine
"""

from litrun.engine_ffi import CtypesLlamaEngine
from litrun.engine import get_backend


def test_ctypes_engine_initialization_fallback():
    # Explicitly test fallback with non-existent library
    engine = CtypesLlamaEngine(model_path="test_model.gguf", lib_path="/tmp/nonexistent_lib.so", threads=2)
    assert not engine.is_native_loaded
    assert engine.threads == 2


def test_ctypes_engine_streaming():
    engine = CtypesLlamaEngine(model_path="test_model.gguf", threads=4)
    chunks = list(engine.stream("Hello edge world", max_tokens=16))
    full_text = "".join(chunks)
    assert "in-process" in full_text.lower()
    assert engine.last_tokens_per_sec > 0.0
    assert engine.last_ttft_ms > 0.0
    engine.close()


def test_get_backend_prefer_ffi():
    backend = get_backend(
        binary_path=None,
        model_path=None,
        prefer_ffi=True,
        allow_mock=True,
    )
    assert backend is not None
