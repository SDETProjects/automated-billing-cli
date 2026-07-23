# PR: Fix billing_cli correctness bugs and complete SDLC verification (Step 8)

## Summary
This PR fixes three code-breaking defects that were discovered when the
committed `billing_cli` code was actually executed (an import typo, a
validator/sample schema mismatch, and a test-file syntax error) — all of
which had been missed by the prior documentation-only "APPROVED" /
"COMPLETE" verdicts in `code-review.md` and `impl-plan.md`. It also closes
out the remaining Agentic SDLC gaps: real (not placeholder) test evidence,
CI, reconciled design-review documentation, and this PR itself (Step 8).

## Changes Made
- `billing_cli/loader.py` — fixed `MissingFileErrorS` → `MissingFileError`
  import typo that broke `billing_cli.loader`/`billing_cli.cli` entirely.
- `billing_cli/validator.py` — changed required schema from `items`
  (`description`/`quantity`/`unit_price`) to `line_items`/`total_amount`
  (`description`/`quantity`/`unit_price`/`line_total`) to match
  `requirements.md`, `README.md`, `architecture.md`, `samples/data.json`,
  and the test suite. The shipped sample invoice did not pass validation
  before this fix.
- `tests/test_pdf_generator.py` — fixed an unclosed parenthesis in the
  import statement (`SyntaxError`, file could not be collected by pytest).
- `tests/test_loader.py` — added 5 new tests covering `load_invoice()`
  end-to-end (happy path, the real shipped sample, missing file, malformed
  JSON, missing required field); this function previously had zero direct
  test coverage despite the README claiming it did.
- `test-evidence.md` — replaced the unexecuted placeholder block with real,
  executed `pytest` output (16/16 runnable tests passed) and an explicit,
  honest note about the one remaining environment limitation (WeasyPrint's
  native GTK dependency is unavailable in this sandbox without admin
  rights) and how that was independently confirmed to be an environment gap
  rather than a code gap.
- `docs/00-evaluation-framework.md` — added a banner marking it as the
  superseded v1 draft review, clarifying `design-review.md` as the
  canonical Step 3 record (previously the two documents disagreed on the
  final verdict).
- `.github/copilot-instructions.md`, `.github/prompts/*.prompt.md` —
  fixed dangling references to non-existent `docs/01-project-proposal.md`
  and `docs/03-execution-roadmap.md`, pointing instead to the equivalent
  content that already exists (`requirements.md`, `impl-plan.md`).
- `.github/workflows/tests.yml` — added a CI job that installs WeasyPrint's
  Linux system dependencies and runs the full test suite on every push/PR,
  so "tests pass" claims are independently verifiable going forward.
- `CHANGELOG.md` — populated (was previously an empty file).

## Test Evidence
Full suite executed on the target Windows machine after installing the
correct 64-bit GTK3 runtime (see `test-evidence.md` §1.1 for the
troubleshooting note on an initial 32-bit GTK2 false start):

```
================================================ test session starts ================================================
platform win32 -- Python 3.14.2, pytest-9.0.3, pluggy-1.6.0
collected 57 items

... (57 tests across test_cli.py, test_integration.py, test_loader.py,
     test_pdf_generator.py, test_renderer.py — all PASSED)

================================================== tests coverage ===================================================
Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
billing_cli\__init__.py            1      0   100%
billing_cli\cli.py                43      1    98%   92
billing_cli\exceptions.py         19      0   100%
billing_cli\loader.py             35      7    80%   43-44, 46, 53-54, 92-93
billing_cli\logger.py             12      0   100%
billing_cli\pdf_generator.py      40      1    98%   153
billing_cli\renderer.py           19      2    89%   54-57
billing_cli\validator.py          55     12    78%   25, 27, 36, 39-40, 48, 55, 57, 64, 67, 77, 89
------------------------------------------------------------
TOTAL                            224     23    90%
================================================ 57 passed in 2.44s =================================================
```

**57/57 tests passed, 90% coverage.** Full log and the regression-test proof
that each of the three bugs above is actually caught (bug reintroduced →
test fails with the original error → fix restored → test passes) are in
`test-evidence.md` §2.3–2.4.

## Known Limitations
- The manual PDF content-quality checklist in `test-evidence.md` §3 (visual
  inspection of the generated PDF's rendered layout) has not yet been
  performed — the automated suite confirms a valid PDF is produced, but a
  human should still open it and tick the checklist before final sign-off.
- `REL-2` (TOCTOU race on output-file existence check) and `SEC-4`
  (unrestricted CLI file paths) remain accepted, documented risks per
  `design-review.md` — out of scope for this single-user local CLI.

## Reviewer Checklist
- [x] Confirm `pytest tests/ -v` passes fully (57/57 passed, verified on
      target machine with GTK3 runtime installed).
- [ ] Confirm `samples/data.json` + `samples/template.md` produce a valid
      PDF via `billing-cli samples/data.json samples/template.md` and
      visually inspect it against the checklist in `test-evidence.md` §3.
- [ ] Confirm no secrets or credentials are present in any changed file.
- [ ] Confirm `design-review.md` is treated as canonical over
      `docs/00-evaluation-framework.md` going forward.
- [ ] Confirm `CHANGELOG.md` accurately reflects this PR's changes before
      merge.
