"""argparse entrypoint, registered as the `chronicle` console script
(see pyproject.toml's [project.scripts])."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..storage.run_store import RunStore
from . import commands

DEFAULT_RUNS_DIR = Path(__file__).resolve().parents[3] / "runs"  # backend/runs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chronicle")
    parser.add_argument(
        "--runs-dir",
        default=str(DEFAULT_RUNS_DIR),
        help="Directory to store/read run state (default: backend/runs)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_generate = subparsers.add_parser("generate", help="Start a new deterministic run for a topic")
    p_generate.add_argument("topic")
    p_generate.add_argument(
        "--fail-at",
        default=None,
        help="Deliberately fail a named stage, for testing resume-after-failure (debug aid, not for real use)",
    )
    p_generate.add_argument(
        "--provider-set",
        choices=["mock", "concert-of-europe"],
        default="mock",
        help="Which stage-function set to run (default: mock, the generic C2 pipeline)",
    )

    p_resume = subparsers.add_parser("resume", help="Resume an existing run")
    p_resume.add_argument("run_id")
    p_resume.add_argument(
        "--provider-set",
        choices=["mock", "concert-of-europe"],
        default="mock",
        help="Which stage-function set to resume with (default: mock)",
    )

    p_inspect = subparsers.add_parser("inspect", help="Show a run's status, stages, and any errors")
    p_inspect.add_argument("run_id")

    p_validate = subparsers.add_parser("validate", help="Validate a GeneratedInvestigation package JSON file")
    p_validate.add_argument("package_path")

    p_corpus = subparsers.add_parser("corpus", help="Inspect and search registered corpora (Phase E2)")
    corpus_sub = p_corpus.add_subparsers(dest="corpus_command", required=True)
    corpus_sub.add_parser("list", help="List registered corpora")
    p_corpus_inspect = corpus_sub.add_parser("inspect", help="Show a corpus's manifest and record counts")
    p_corpus_inspect.add_argument("corpus_id")
    p_corpus_search = corpus_sub.add_parser("search", help="Run search_passages against a corpus")
    p_corpus_search.add_argument("corpus_id")
    p_corpus_search.add_argument("query")

    p_tools = subparsers.add_parser("tools", help="Inspect and invoke the typed tool registry (Phase E2)")
    tools_sub = p_tools.add_subparsers(dest="tools_command", required=True)
    tools_sub.add_parser("list", help="List registered tools")
    p_tools_invoke = tools_sub.add_parser("invoke", help="Invoke a tool by name")
    p_tools_invoke.add_argument("tool_name")
    p_tools_invoke.add_argument("--corpus-id", required=True)
    p_tools_invoke.add_argument(
        "--input",
        required=True,
        help="JSON input for the tool (corpusId filled in from --corpus-id if omitted)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        return commands.cmd_validate(args.package_path)

    if args.command == "corpus":
        if args.corpus_command == "list":
            return commands.cmd_corpus_list()
        if args.corpus_command == "inspect":
            return commands.cmd_corpus_inspect(args.corpus_id)
        if args.corpus_command == "search":
            return commands.cmd_corpus_search(args.corpus_id, args.query)

    if args.command == "tools":
        if args.tools_command == "list":
            return commands.cmd_tools_list()
        if args.tools_command == "invoke":
            return commands.cmd_tools_invoke(args.tool_name, args.corpus_id, args.input)

    store = RunStore(Path(args.runs_dir))
    if args.command == "generate":
        return commands.cmd_generate(store, args.topic, args.fail_at, args.provider_set)
    if args.command == "resume":
        return commands.cmd_resume(store, args.run_id, args.provider_set)
    if args.command == "inspect":
        return commands.cmd_inspect(store, args.run_id)

    parser.error(f"Unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
