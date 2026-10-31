"""
litrun Edge Vector Search & Local RAG Unit Tests
"""

import os
import tempfile
from click.testing import CliRunner
from litrun.rag import (
    compute_lightweight_embedding,
    cosine_similarity,
    EdgeVectorStore,
    build_rag_augmented_prompt,
)
from litrun.cli.cmd_embed import embed_cmd
from litrun.cli.cmd_run import run_cmd


def test_compute_lightweight_embedding():
    vec1 = compute_lightweight_embedding("hydraulic pressure valve failure code E-04")
    vec2 = compute_lightweight_embedding("hydraulic valve problem alert E-04")
    vec3 = compute_lightweight_embedding("strawberry cake recipe with sugar")

    assert len(vec1) == 128
    sim_close = cosine_similarity(vec1, vec2)
    sim_far = cosine_similarity(vec1, vec3)

    assert sim_close > sim_far
    assert sim_close > 0.40


def test_edge_vector_store_crud():
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp_db:
        store = EdgeVectorStore(db_path=tmp_db.name)

        doc = """
        Industrial Centrifugal Pump Diagnostic Manual:
        Error Code E-04 indicates hydraulic pressure drop below 15 PSI.
        Action: Inspect intake filter and verify secondary seal integrity.
        Normal operating RPM is 1800 to 2400.
        """
        chunks = store.add_document("pump_manual.txt", doc, chunk_size=20, overlap=5)
        assert chunks > 0

        sources = store.list_sources()
        assert len(sources) == 1
        assert sources[0]["source"] == "pump_manual.txt"

        # Search
        results = store.search("What does code E-04 mean?", top_k=2)
        assert len(results) > 0
        assert "E-04" in results[0]["text"]
        assert results[0]["similarity"] > 0.20

        # Clear
        store.clear()
        assert len(store.list_sources()) == 0


def test_build_rag_augmented_prompt():
    contexts = [
        {"source": "manual.md", "text": "Pump operating range is 10-50 PSI.", "similarity": 0.85}
    ]
    augmented = build_rag_augmented_prompt("Check pump pressure", contexts)
    assert "LOCAL KNOWLEDGE BASE" in augmented
    assert "manual.md" in augmented
    assert "10-50 PSI" in augmented


def test_cli_embed_and_query():
    runner = CliRunner()
    # Ingest raw text
    res1 = runner.invoke(embed_cmd, ["--text", "Emergency shutoff switch is on pin 21", "--source", "safety_guide"])
    assert res1.exit_code == 0
    assert "Ingested raw text" in res1.output

    # List sources
    res2 = runner.invoke(embed_cmd, ["--list"])
    assert res2.exit_code == 0
    assert "safety_guide" in res2.output

    # Query search
    res3 = runner.invoke(embed_cmd, ["--query", "Where is the emergency switch?"])
    assert res3.exit_code == 0
    assert "safety_guide" in res3.output

    # Clear
    res4 = runner.invoke(embed_cmd, ["--clear"])
    assert res4.exit_code == 0
    assert "Cleared all vector embeddings" in res4.output
