# Automated Billing CLI (Invoice Generator)

An offline, Python 3.10+ command-line tool that converts JSON invoice data and a
Jinja2/Markdown template into a styled PDF invoice. Built following the
phase-executor TDD workflow described in `.github/prompts/`, with every module
implemented against `requirements.md` and `docs/02-architecture-spec.md`.

## Features

- Loads and validates invoice JSON against a strict schema (required fields
  and types; see FR-2/FR-3 in `requirements.md`).
- Merges JSON data into a Jinja2 Markdown template, rendering `line_items` as
  a Markdown table.
- Converts the rendered Markdown to a minimalist, A4 PDF (no external
  CSS/branding).
- Auto-creates `./output/` and refuses to overwrite an existing invoice PDF.
- Distinct, human-readable error messages for missing files, malformed JSON,
  and schema violations — always exits with code `1` on failure, `0` on
  success.
- `--verbose` flag for DEBUG-level console logging.
- 100% offline: no network calls, no external API dependencies at runtime.

## Architecture

The pipeline is a strict linear sequence orchestrated by `billing_cli/cli.py`:

```
load_invoice -> load_template -> render_markdown -> markdown_to_html
             -> resolve_output_path -> generate_pdf
```

| Module | Responsibility |
|---|---|
| `loader.py` | Reads and JSON-decodes the invoice file; validates schema (FR-2/FR-3). |
| `renderer.py` | Renders the Jinja2 template in a `SandboxedEnvironment` (SSTI mitigation) and converts Markdown to HTML. |
| `pdf_generator.py` | Converts HTML to a styled PDF via WeasyPrint with a restricted `url_fetcher` (no remote resource fetching) and atomic file writes. |
| `exceptions.py` | `BillingCLIError` hierarchy: `MissingFileError`, `InvalidJSONError`, `SchemaValidationError`, `OutputExistsError`. |
| `logger.py` | Console-only logging; `--verbose` toggles DEBUG level. |
| `cli.py` | Wires the pipeline together; catches `BillingCLIError` subclasses and any unexpected exception as a last-resort safety net. |

Security and reliability hardening (per architecture spec):
- Sandboxed Jinja2 rendering prevents server-side template injection (SSTI).
- PDF rendering blocks arbitrary URL fetching.
- Invoice IDs are sanitized before being used in output file paths.
- Writes are atomic; no partial/corrupt PDF files are ever left behind.

## Installation

```bash
git clone <repository-url>
cd <repository-directory>
pip install -e .
```

Requires Python 3.10+. Dependencies are managed via `pyproject.toml`.

## Usage

```bash
python -m billing_cli.cli <data.json> <template.md> [--verbose]
```

**Arguments:**
- `data.json` – path to the invoice JSON file (must contain `invoice_id`,
  `date`, `client_name`, `line_items`, `total_amount`).
- `template.md` – path to a Jinja2-flavored Markdown template.
- `--verbose` – optional flag to enable DEBUG-level logging.

**Example:**

```bash
python -m billing_cli.cli invoices/inv-001.json templates/invoice.md
```

On success, the tool prints:

```
Invoice PDF generated: ./output/invoice_INV-001.pdf
```

and exits with code `0`. On any failure (missing file, malformed JSON,
schema violation, or an existing output file), it prints a distinct
human-readable error to stderr and exits with code `1`.

## Testing

The test suite follows TDD principles: unit tests were written before each
module's implementation, plus a real (non-mocked) integration/E2E suite.

```bash
pytest tests/ -v
```

| Test file | Scope |
|---|---|
| `test_loader.py` | JSON loading and schema validation (unit). |
| `test_renderer.py` | Jinja2 template rendering and Markdown-to-HTML conversion (unit). |
| `test_pdf_generator.py` | HTML-to-PDF generation and atomic writes (unit). |
| `test_cli.py` | CLI orchestration, argument parsing, and error handling, with pipeline stages mocked (unit). |
| `test_integration.py` | Full pipeline against real temp files: real PDF output, output-directory creation, no-overwrite behavior, and file/schema error messages (integration/E2E). |

## Out of Scope

As defined in `requirements.md`:
- Mathematical reconciliation of `line_items` totals against `total_amount`.
- Multi-currency or locale-specific currency formatting.
- Custom branding, logos, or external CSS styling in the PDF.
- File overwrite/versioning support (e.g., auto-incrementing filenames).
- Network/API-based invoice data sources.
- Authentication, multi-user, or SaaS-style deployment.
