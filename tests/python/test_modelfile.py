"""
Unit tests for litrun Modelfile parsing, packaging, and custom model execution.
"""

import os
import shutil
import tempfile
from click.testing import CliRunner
from litrun.modelfile import (
    ParsedModelfile,
    ModelfileParser,
    CustomModelManifest,
    save_custom_model,
    get_custom_model,
    list_custom_models,
    delete_custom_model,
    export_custom_model_pack,
    import_custom_model_pack,
    get_custom_models_root,
)
from litrun.model import Model
from litrun.cli.main import cli


def test_modelfile_parser_syntax():
    content = """
    # Edge Autonomous Rover Agent
    FROM smollm2-135m
    PARAMETER temperature 0.35
    PARAMETER max_tokens 128
    PARAMETER stream true
    PARAMETER top_p 0.9

    SYSTEM \"\"\"You are Rover-01, an autonomous embedded ground vehicle.
    Always prioritize safety protocols and emit structured JSON actions.\"\"\"

    ADAPTER ./adapters/rover_nav.litlora
    LICENSE \"\"\"Apache-2.0\"\"\"
    MESSAGE user "Report status"
    MESSAGE assistant "All telemetry nominal."
    """

    parsed = ModelfileParser.parse(content)
    assert parsed.base_model == "smollm2-135m"
    assert parsed.parameters["temperature"] == 0.35
    assert parsed.parameters["max_tokens"] == 128
    assert parsed.parameters["stream"] is True
    assert parsed.parameters["top_p"] == 0.9
    assert "Rover-01" in parsed.system_prompt
    assert "rover_nav.litlora" in parsed.adapter_path
    assert parsed.license == "Apache-2.0"
    assert len(parsed.messages) == 2


def test_custom_model_registry_crud_and_packing():
    tag = "test-agent:v1.0"
    content = """
    FROM smollm2-135m
    PARAMETER temperature 0.2
    SYSTEM "Embedded industrial controller agent."
    """
    parsed = ModelfileParser.parse(content)
    manifest = save_custom_model(tag, parsed)
    assert manifest.tag == tag
    assert manifest.base_model == "smollm2-135m"

    # Get
    retrieved = get_custom_model(tag)
    assert retrieved is not None
    assert retrieved.tag == tag
    assert retrieved.parameters.get("temperature") == 0.2

    # List
    all_models = list_custom_models()
    assert any(m.tag == tag for m in all_models)

    # Export & Import Pack
    with tempfile.TemporaryDirectory() as tmpdir:
        pack_path = os.path.join(tmpdir, "test_pack.litpack")
        exported_path = export_custom_model_pack(tag, pack_path)
        assert os.path.isfile(exported_path)

        imported_manifest = import_custom_model_pack(exported_path, tag="imported-agent:latest")
        assert imported_manifest.tag == "imported-agent:latest"
        assert imported_manifest.base_model == "smollm2-135m"

        # Cleanup imported
        delete_custom_model("imported-agent:latest")

    # Delete
    deleted = delete_custom_model(tag)
    assert deleted is True
    assert get_custom_model(tag) is None


def test_model_load_custom_model_resolution():
    tag = "custom-drone:v1"
    content = """
    FROM smollm2-135m
    PARAMETER temperature 0.15
    PARAMETER max_tokens 64
    SYSTEM "Drone-Alpha aerial navigation flight computer."
    """
    parsed = ModelfileParser.parse(content)
    save_custom_model(tag, parsed)

    try:
        model = Model.load(tag, allow_mock=True)
        assert model.entry.id == "smollm2-135m"
        assert hasattr(model, "custom_manifest")
        assert model.custom_manifest.tag == tag
        assert "Drone-Alpha" in model.session.system_prompt
        assert model.default_parameters["temperature"] == 0.15

        res = model.generate("Status check")
        assert len(res) > 0
    finally:
        delete_custom_model(tag)


def test_cli_create_commands():
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        modelfile = os.path.join(tmpdir, "Modelfile")
        with open(modelfile, "w") as f:
            f.write("FROM smollm2-135m\nSYSTEM \"CLI Test\"\n")

        # Create
        res = runner.invoke(cli, ["create", "-f", modelfile, "-t", "cli-test:v1"])
        assert res.exit_code == 0
        assert "Successfully built custom model" in res.output

        # List
        res_list = runner.invoke(cli, ["create", "list"])
        assert res_list.exit_code == 0
        assert "cli-test:v1" in res_list.output

        # Inspect
        res_insp = runner.invoke(cli, ["create", "inspect", "cli-test:v1"])
        assert res_insp.exit_code == 0
        assert "CLI Test" in res_insp.output

        # Clean
        delete_custom_model("cli-test:v1")
