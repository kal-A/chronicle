# Continuous integration

[`ci.yml`](./ci.yml) runs on every push to `master` / `phase-e-ai-core`, on every
pull request into `master`, and on manual dispatch. Two independent jobs, both on
`ubuntu-latest`, both using the repository's own canonical commands.

## Jobs

### `backend` — Python 3.14

| Step | Command |
|---|---|
| Install | `pip install -e ".[test]"` (from `backend/`) |
| Test | `pytest` |

`pip` downloads are cached (keyed on `backend/pyproject.toml`). The test suite is the
backend's static gate — there is no separate linter/type-checker configured for the
backend, so nothing is skipped by omitting one. The suite includes the
anti-topic-branching guard (`tests/ai/tools/test_no_topic_branching_guard.py`).

### `frontend` — Node 24

| Step | Command |
|---|---|
| Install | `npm ci` (locked, from `package-lock.json`) |
| Lint | `npm run lint` (oxlint) |
| Type-check | `npm run typecheck` (`tsc -b --noEmit`) |
| Unit tests | `npx vitest run` |
| Build | `npm run build` (`tsc -b && vite build`) |

`npm` downloads are cached (keyed on `package-lock.json`).

## Excluded from CI (by design)

These tests exercise real models, external services, or a full browser, so they cannot
run on a stock CI runner without a GPU/daemon/credentials. **None** is weakened or
deleted — each is deselected and runnable locally.

| Excluded | Why it can't run in stock CI | How it's gated / how to run it |
|---|---|---|
| `local_ollama_integration` (backend) | Needs a real local **Ollama** daemon + a pulled open-weight model. | Deselected by `addopts` in `backend/pyproject.toml`. Run locally: `pytest -m local_ollama_integration -s`. Self-skips (does not fail) when Ollama is unreachable. |
| `live_network_integration` (backend) | Hits **live** free source APIs (Wikipedia, Gutenberg, Internet Archive) — non-deterministic and network-dependent. | Deselected by the same `addopts`. Run locally: `pytest -m live_network_integration -s`. Self-skips when offline. |
| Playwright end-to-end (`npm run test:e2e`) | Full user-journey tests that build + preview the app and drive a real Chromium; they belong to a separate journey suite, not the frontend unit gate. | Not part of the `frontend` job (scope: unit tests). Run locally: `npx playwright install` then `npm run test:e2e`. Can be added as a dedicated job later with `npx playwright install --with-deps`. |

No CI step requires a personal credential, token, API key, or secret.

## Notes

- **Versions** are pinned to what the project is developed against: Python 3.14
  (`requires-python >=3.11`) and Node 24 (matches `@types/node`, satisfies Vite 8).
- **Local vitest tip:** on a low-RAM machine the default forks pool can time out
  spawning workers (`Failed to start forks worker`). This is an environment limit, not
  a test failure — run `npx vitest run --no-file-parallelism` locally. CI runners have
  enough resources for the default pool.
