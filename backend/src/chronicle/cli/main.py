"""argparse entrypoint, registered as the `chronicle` console script
(see pyproject.toml's [project.scripts])."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..storage.run_store import RunStore
from . import commands
from . import evaluation as evaluation_cmds

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

    p_evaluate = subparsers.add_parser(
        "evaluate", help="Run the E7 comparative evaluation harness (Phase E7)"
    )
    evaluate_sub = p_evaluate.add_subparsers(dest="evaluate_command", required=True)
    p_eval_run = evaluate_sub.add_parser("run", help="Execute a benchmark profile, resuming if interrupted")
    p_eval_run.add_argument(
        "--profile", default="deterministic_full", help="Evaluation profile (default: deterministic_full)"
    )
    p_eval_run.add_argument(
        "--provider", default="deterministic", help="Model provider (Slice 1: deterministic)"
    )
    p_eval_run.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parents[3] / "evaluation-runs" / "latest"),
        help="Run output directory (default: backend/evaluation-runs/latest)",
    )
    p_eval_run.add_argument("--cases", default=None, help="Comma-separated caseId/legacy-alias filter")
    p_eval_run.add_argument("--strategies", default=None, help="Comma-separated strategy id filter")
    p_eval_run.add_argument("--max-cases", type=int, default=None, help="Cap the number of cases")
    p_eval_run.add_argument("--repeats", type=int, default=1, help="Repeats per identity (default: 1)")
    p_eval_status = evaluate_sub.add_parser("status", help="Report a run's completed/remaining progress")
    p_eval_status.add_argument("run", help="Run output directory")
    p_eval_report = evaluate_sub.add_parser("report", help="Score a run into JSON + Markdown reports")
    p_eval_report.add_argument("run", help="Run output directory")
    p_eval_report.add_argument("--json", dest="output_json", default=None, help="JSON report path")
    p_eval_report.add_argument("--markdown", dest="output_md", default=None, help="Markdown report path")
    p_eval_review = evaluate_sub.add_parser(
        "export-review", help="Write a single-reviewer blinded export (answers only)"
    )
    p_eval_review.add_argument("run", help="Run output directory")
    p_eval_review.add_argument("--output", required=True, help="Blinded review file path")
    p_eval_review.add_argument("--key", default=None, help="Blinding key path (default: alongside --output)")
    p_eval_review.add_argument("--seed", type=int, default=0, help="Answer-order shuffle seed")

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

    if args.command == "evaluate":
        if args.evaluate_command == "run":
            return evaluation_cmds.cmd_evaluate_run(
                profile=args.profile,
                provider=args.provider,
                output=args.output,
                cases=args.cases,
                strategies=args.strategies,
                max_cases=args.max_cases,
                repeats=args.repeats,
            )
        if args.evaluate_command == "status":
            return evaluation_cmds.cmd_evaluate_status(args.run)
        if args.evaluate_command == "report":
            return evaluation_cmds.cmd_evaluate_report(args.run, args.output_json, args.output_md)
        if args.evaluate_command == "export-review":
            return evaluation_cmds.cmd_evaluate_export_review(
                args.run, args.output, args.seed, args.key
            )

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
