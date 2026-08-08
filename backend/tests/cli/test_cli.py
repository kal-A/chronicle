import io
import json
from pathlib import Path

import pytest

from chronicle.cli import commands
from chronicle.cli import main as cli_main
from chronicle.storage.run_store import RunStore

REPO_ROOT = Path(__file__).resolve().parents[3]
GOLDEN_FIXTURE = REPO_ROOT / "fixtures" / "blank-cheque.golden-investigation.json"
INVALID_FIXTURE = REPO_ROOT / "fixtures" / "contracts" / "invalid" / "unsupported-version.json"


def test_generate_then_inspect_reports_partial(tmp_path):
    # MOCK_STAGE_FNS's generic providers honestly produce no map data for a
    # synthetic topic, so the package (and the run) come out "partial", not
    # "ready" — see providers/mock/geography.py's abstention. A "partial"
    # exit code is still 0: the pipeline itself didn't fail.
    store = RunStore(tmp_path)
    out = io.StringIO()

    exit_code = commands.cmd_generate(store, "Concert of Europe", out=out)
    assert exit_code == 0
    run_id = out.getvalue().splitlines()[0].removeprefix("Run ")

    inspect_out = io.StringIO()
    inspect_exit = commands.cmd_inspect(store, run_id, out=inspect_out)
    assert inspect_exit == 0
    assert "status: partial" in inspect_out.getvalue()
    assert "VERIFIED" in inspect_out.getvalue()


def test_resume_on_completed_run_is_a_no_op_success(tmp_path):
    store = RunStore(tmp_path)
    out = io.StringIO()
    commands.cmd_generate(store, "Concert of Europe", out=out)
    run_id = out.getvalue().splitlines()[0].removeprefix("Run ")

    resume_out = io.StringIO()
    exit_code = commands.cmd_resume(store, run_id, out=resume_out)

    assert exit_code == 0
    assert "status: partial" in resume_out.getvalue()


def test_resume_unknown_run_id_reports_not_found(tmp_path):
    store = RunStore(tmp_path)
    out = io.StringIO()

    exit_code = commands.cmd_resume(store, "does-not-exist", out=out)

    assert exit_code == 2
    assert "does-not-exist" in out.getvalue()


def test_generate_with_fail_at_produces_failed_status(tmp_path):
    store = RunStore(tmp_path)
    out = io.StringIO()

    exit_code = commands.cmd_generate(store, "A failing run", fail_at="CORPUS_PREPARED", out=out)

    assert exit_code == 1
    assert "status: failed" in out.getvalue()
    assert "failed stage: CORPUS_PREPARED" in out.getvalue()


def test_generate_with_unknown_fail_at_stage_is_rejected(tmp_path):
    store = RunStore(tmp_path)
    out = io.StringIO()

    exit_code = commands.cmd_generate(store, "A run", fail_at="NOT_A_REAL_STAGE", out=out)

    assert exit_code == 2
    assert "Unknown stage" in out.getvalue()


def test_inspect_failed_run_shows_error_detail(tmp_path):
    store = RunStore(tmp_path)
    generate_out = io.StringIO()
    commands.cmd_generate(store, "A failing run", fail_at="CORPUS_PREPARED", out=generate_out)
    run_id = generate_out.getvalue().splitlines()[0].removeprefix("Run ")

    inspect_out = io.StringIO()
    commands.cmd_inspect(store, run_id, out=inspect_out)

    assert "RuntimeError" in inspect_out.getvalue()
    assert "attempt count: 1" in inspect_out.getvalue()


def test_validate_accepts_the_real_golden_fixture():
    out = io.StringIO()
    exit_code = commands.cmd_validate(str(GOLDEN_FIXTURE), out=out)

    assert exit_code == 0
    assert 'VALID: packageId="blank-cheque-golden"' in out.getvalue()


def test_validate_rejects_a_known_invalid_fixture():
    out = io.StringIO()
    exit_code = commands.cmd_validate(str(INVALID_FIXTURE), out=out)

    assert exit_code == 1
    assert "INVALID" in out.getvalue()
    assert "Unsupported GeneratedInvestigation schema version" in out.getvalue()


def test_generate_with_concert_of_europe_provider_set_produces_real_content(tmp_path):
    store = RunStore(tmp_path)
    out = io.StringIO()

    exit_code = commands.cmd_generate(
        store,
        "The Concert of Europe and Revolutionary Intervention",
        provider_set="concert-of-europe",
        out=out,
    )

    assert exit_code == 0
    run_id = out.getvalue().splitlines()[0].removeprefix("Run ")

    inspect_out = io.StringIO()
    commands.cmd_inspect(store, run_id, out=inspect_out)
    assert "provider set version: d0.4-concert-of-europe-v2" in inspect_out.getvalue()

    package_path = store.load_run(run_id).outputPackagePath
    assert package_path is not None
    validate_out = io.StringIO()
    validate_exit = commands.cmd_validate(package_path, out=validate_out)
    assert validate_exit == 0
    assert 'packageId="concert-of-europe-1814-1822"' in validate_out.getvalue()


def test_validate_missing_file_reports_cleanly():
    out = io.StringIO()
    exit_code = commands.cmd_validate("no/such/file.json", out=out)

    assert exit_code == 2
    assert "No file found" in out.getvalue()


def test_corpus_list_reports_registered_corpora():
    out = io.StringIO()

    assert commands.cmd_corpus_list(out=out) == 0
    rendered = out.getvalue()
    assert "blank-cheque-golden" in rendered
    assert "concert-of-europe-1814-1822" in rendered
    assert "schema version: 1.0.0" in rendered


def test_corpus_inspect_reports_identity_and_record_counts():
    out = io.StringIO()

    assert commands.cmd_corpus_inspect("blank-cheque-golden", out=out) == 0
    rendered = out.getvalue()
    assert "Corpus blank-cheque-golden" in rendered
    assert "package hash:" in rendered
    assert "passages:" in rendered
    assert "claims:" in rendered


def test_corpus_search_renders_current_role_aware_hit_contract():
    out = io.StringIO()

    assert commands.cmd_corpus_search("blank-cheque-golden", "Austria", out=out) == 0
    rendered = out.getvalue()
    assert 'Search "Austria" in blank-cheque-golden:' in rendered
    assert "score=" in rendered
    assert "factors=" in rendered


def test_tools_list_renders_planner_safe_specs():
    out = io.StringIO()

    assert commands.cmd_tools_list(out=out) == 0
    rendered = out.getvalue()
    assert "search_passages" in rendered
    assert "use when:" in rendered
    assert "avoid when:" in rendered
    assert "maximum output characters: 16000" in rendered
    assert "input schema:" in rendered


def test_tools_invoke_prints_valid_json():
    out = io.StringIO()

    exit_code = commands.cmd_tools_invoke(
        "search_passages",
        "blank-cheque-golden",
        json.dumps({"query": "Austria"}),
        out=out,
    )

    assert exit_code == 0
    result = json.loads(out.getvalue())
    assert result["corpusId"] == "blank-cheque-golden"
    assert result["returnedCount"] == len(result["hits"])


@pytest.mark.parametrize("input_json", ["[]", "null", '"query"', "3", "true"])
def test_tools_invoke_rejects_non_object_json(input_json):
    out = io.StringIO()

    exit_code = commands.cmd_tools_invoke(
        "search_passages", "blank-cheque-golden", input_json, out=out
    )

    assert exit_code == 2
    assert "--input must be a JSON object" in out.getvalue()


def test_tools_invoke_rejects_malformed_json():
    out = io.StringIO()

    exit_code = commands.cmd_tools_invoke(
        "search_passages", "blank-cheque-golden", "{not-json", out=out
    )

    assert exit_code == 2
    assert "--input is not valid JSON" in out.getvalue()


def test_corpus_commands_report_unknown_corpus_cleanly():
    inspect_out = io.StringIO()
    search_out = io.StringIO()

    assert commands.cmd_corpus_inspect("not-registered", out=inspect_out) == 2
    assert commands.cmd_corpus_search("not-registered", "query", out=search_out) == 2
    assert "not-registered" in inspect_out.getvalue()
    assert "not-registered" in search_out.getvalue()


def test_tools_invoke_reports_unknown_tool_and_invalid_input_cleanly():
    unknown_out = io.StringIO()
    invalid_out = io.StringIO()

    assert commands.cmd_tools_invoke("not-a-tool", "blank-cheque-golden", "{}", out=unknown_out) == 1
    assert "UnknownToolError" in unknown_out.getvalue()
    assert commands.cmd_tools_invoke(
        "search_passages", "blank-cheque-golden", '{"query": "   "}', out=invalid_out
    ) == 1
    assert "MalformedToolInputError" in invalid_out.getvalue()


@pytest.mark.parametrize(
    ("argv", "function_name", "expected_args"),
    [
        (["corpus", "list"], "cmd_corpus_list", ()),
        (["corpus", "inspect", "corpus-a"], "cmd_corpus_inspect", ("corpus-a",)),
        (["corpus", "search", "corpus-a", "term"], "cmd_corpus_search", ("corpus-a", "term")),
        (["tools", "list"], "cmd_tools_list", ()),
        (
            ["tools", "invoke", "search_passages", "--corpus-id", "corpus-a", "--input", "{}"],
            "cmd_tools_invoke",
            ("search_passages", "corpus-a", "{}"),
        ),
    ],
)
def test_phase_e2_parser_routes_to_command(monkeypatch, argv, function_name, expected_args):
    called = []

    def fake(*args):
        called.append(args)
        return 17

    monkeypatch.setattr(commands, function_name, fake)
    assert cli_main.main(argv) == 17
    assert called == [expected_args]
