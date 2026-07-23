# Changelog

All notable changes to the Billing CLI capstone project are documented here.

## [0.1.1] - 2026-07-23

### Fixed
- **`billing_cli/loader.py`**: fixed an import typo (`MissingFileErrorS` →
  `MissingFileError`) that broke every import of `billing_cli.loader` and,
  transitively, `billing_cli.cli` and the `billing-cli` console-script
  entry point.
- **`billing_cli/validator.py`**: aligned the required-field schema to
  `line_items` / `total_amount` / `line_total`, matching
  `requirements.md`, `README.md`, `architecture.md`, `samples/data.json`,
  and the test suite. The validator previously required a divergent
  `items` schema, causing the shipped sample invoice to fail validation.
- **`tests/test_pdf_generator.py`**: fixed an unclosed parenthesis in the
  module's import statement that caused a `SyntaxError`, preventing pytest
  from collecting the file at all.

### Added
- Regression tests in `tests/test_loader.py` covering `load_invoice()`
  end-to-end (previously untested): happy path, the shipped sample data,
  missing file, malformed JSON, and missing required field.
- `.github/workflows/tests.yml`: CI workflow running the test suite on
  push/PR.

### Changed
- `test-evidence.md` replaced with real, executed `pytest` output (was
  previously an unexecuted placeholder).
- `docs/00-evaluation-framework.md` marked as a superseded v1 draft, with
  `design-review.md` clarified as the canonical Step 3 record, resolving a
  verdict mismatch between the two documents.
- `.github/copilot-instructions.md` and `.github/prompts/*.prompt.md`
  updated to reference `requirements.md` and `impl-plan.md` (which exist)
  instead of the non-existent `docs/01-project-proposal.md` and
  `docs/03-execution-roadmap.md`.

## [0.1.0] - 2026-07-23

### Added
- Initial implementation of the Billing CLI: JSON invoice + Jinja2/Markdown
  template → sandboxed render → WeasyPrint PDF pipeline.
- Full capstone SDLC artifact chain: `requirements.md`, `architecture.md`,
  `design-review.md`, `impl-plan.md`, `code-review.md`, `test-evidence.md`.
