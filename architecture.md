# System Architecture: Automated Billing CLI

> Canonical, approved architecture document for the capstone SDLC Step 2
> ("Architecture"). This is the root-level deliverable named per the task
> brief. The detailed working spec lives at `docs/02-architecture-spec.md`
> and is kept in sync with this file; this file is the authoritative,
> reviewer-facing summary referenced by `design-review.md` and `impl-plan.md`.

## 1. Overview

The Automated Billing CLI is an offline, single-user command-line tool that
converts a JSON invoice payload and a Jinja2/Markdown template into a styled
PDF invoice. It was designed in direct response to the functional and
non-functional requirements captured in `requirements.md`.

## 2. Component Diagram

```
                 +----------------+
                 |     cli.py     |  (entry point / orchestrator)
                 +--------+-------+
                          |
        +---------+---------+---------+----------+
        |         |         |         |          |
        v         v         v         v          v
  loader.py  validator.py renderer.py pdf_generator.py exceptions.py
   (I/O)      (schema)   (Jinja2/MD)   (HTML->PDF)   (error model)
        \_________________________________________/
                          |
                    logger.py (cross-cutting)
```

Data flow (sequence):

```
User -> cli.py: run(invoice.json, template.md, --verbose)
cli.py -> loader.py: load_invoice(path) -> dict
cli.py -> loader.py: load_template(path) -> str
cli.py -> validator.py: validate_schema(dict) -> raises SchemaValidationError | ok
cli.py -> renderer.py: render_markdown(template_str, data) -> rendered_md
cli.py -> renderer.py: markdown_to_html(rendered_md) -> html
cli.py -> pdf_generator.py: resolve_output_path(invoice_id) -> path
cli.py -> pdf_generator.py: generate_pdf(html, path) -> writes PDF atomically
cli.py -> stdout: "Invoice PDF generated: <path>" (exit 0)
           | on any BillingCLIError or unexpected exception
           v
cli.py -> stderr: human-readable message (exit 1)
```

## 3. Technology Choices & Justification

| Layer | Technology | Justification |
|---|---|---|
| CLI Parsing | `argparse` (stdlib) | Zero external dependency; sufficient for 2 positional args + 1 flag. |
| JSON Parsing | `json` (stdlib) | Native, raises `json.JSONDecodeError` cleanly for malformed JSON. |
| Schema Validation | Custom validator module | Only 5 required fields with simple types; a full schema library is over-engineering for this scope. |
| Templating | `jinja2` (`sandbox.SandboxedEnvironment`) | Explicitly required; sandboxed environment prevents SSTI by restricting attribute/introspection access. |
| Markdown -> HTML | `markdown` (Python-Markdown) | Lightweight library to convert merged Markdown (incl. tables via `tables` extension) into HTML. |
| HTML -> PDF | `WeasyPrint` (with locked-down `url_fetcher`) | Pure-Python/CSS PDF rendering, fully offline; custom fetcher blocks all remote/local resource resolution to guarantee the offline NFR. |
| Packaging | `pyproject.toml` + `pip` | Standard modern Python packaging. |

## 4. Component Responsibilities

### 4.1 `cli.py` (Entry Point)
- Parses CLI arguments (`data.json` path, `template.md` path, `--verbose` flag) via `argparse`.
- Orchestrates the pipeline: Loader -> Validator -> Renderer -> PDFGenerator.
- Catches all custom exceptions at the top level, prints the associated human-readable message, exits code `1`. On success, prints `Invoice PDF generated: <path>`, exits `0`.

### 4.2 `loader.py`
- `load_invoice(path)`: confirms file exists, reads with `encoding="utf-8"` explicitly, parses JSON (raises `InvalidJSONError` on syntax errors).
- `load_template(path)`: confirms template file exists, reads with `encoding="utf-8"` explicitly, raises `MissingFileError` if missing.

### 4.3 `validator.py`
- `validate_schema(data)`: checks presence and types of the 5 required fields (`invoice_id`, `date`, `client_name`, `line_items`, `total_amount`), raises `SchemaValidationError` naming the specific field.

### 4.4 `renderer.py` (Hardened)
- Uses `jinja2.sandbox.SandboxedEnvironment` (not the default `Environment`/`Template`) to load and render the template string, mitigating Server-Side Template Injection (SSTI).
- `render_markdown(template_str, data)`.
- `markdown_to_html(md_str)`: converts Markdown (with `tables` extension) to an HTML fragment wrapped in a minimal HTML document with inline `<style>` for A4 size and basic table borders.

### 4.5 `pdf_generator.py` (Hardened)
- `sanitize_invoice_id(invoice_id)`: strips/rejects any character outside `[A-Za-z0-9_-]` before it is used in a filesystem path, preventing path traversal.
- `resolve_output_path(invoice_id)`: builds `./output/invoice_<sanitized_id>.pdf`; creates `./output/` via `os.makedirs(exist_ok=True)`; raises `OutputExistsError` if the target PDF already exists.
- `generate_pdf(html_str, output_path)`: configures `WeasyPrint.HTML(string=html_str, url_fetcher=blocking_fetcher)` where `blocking_fetcher` rejects all `http(s)://` and `file://` resource resolution, enforcing the offline NFR. Writes to a temp file first, then atomically `os.replace()`s it to the final path only after a fully successful write; on exception, the temp file is deleted.

### 4.6 `exceptions.py`
- Custom exception hierarchy: `BillingCLIError` (base) -> `MissingFileError`, `InvalidJSONError`, `SchemaValidationError`, `OutputExistsError`. Each carries a pre-formatted human-readable message consumed by `cli.py`.

### 4.7 `logger.py`
- Thin wrapper around stdlib `logging` configured for console-only output; toggles DEBUG-level output when `--verbose` is set.

## 5. Risks and Assumptions Carried Forward

See `design-review.md` for the full risk register (SEC-1..4, REL-1..3, SCALE-1)
and the design decisions applied to mitigate or explicitly accept each risk.
This architecture reflects the **v2, post-design-review** state: the sandboxed
template environment, restricted PDF `url_fetcher`, invoice-id sanitization,
atomic writes, and explicit UTF-8 encoding were all added in response to that
review.

## 6. Out of Scope

- Mathematical reconciliation of `line_items` totals against `total_amount`.
- Multi-currency or locale-specific currency formatting.
- Custom branding, logos, or external CSS styling in the PDF.
- File overwrite/versioning support (e.g., auto-incrementing filenames).
- Network/API-based invoice data sources.
- Authentication, multi-user, or SaaS-style deployment.
