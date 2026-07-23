# Test Evidence: Automated Billing CLI

> Root-level deliverable for capstone SDLC Step 7 ("Verify"). Documents the
> exact verification procedure and the **real, executed** results for both
> the automated test suite (code) and the generated PDF output (content
> quality check).

## 1. History (Transparency)

This document went through three states before reaching the current one:

1. **Original state:** shipped an unexecuted placeholder result block,
   with an explicit note that no terminal access was available.
2. **First real run:** executed in a Python 3.14 environment with
   `pytest`, `jinja2`, `markdown`, and `weasyprint` installed. This run
   uncovered and fixed three pre-existing defects in the committed code
   (see `CHANGELOG.md` and `code-review.md` §8 for full detail):
   1. `billing_cli/loader.py` imported a non-existent `MissingFileErrorS`
      (typo) instead of `MissingFileError`, breaking every import of
      `billing_cli.loader` / `billing_cli.cli`.
   2. `billing_cli/validator.py` required a schema field `items` while
      every other artifact (requirements.md, README.md, architecture.md,
      `samples/data.json`, most tests) used `line_items` / `total_amount`
      / `line_total` — the shipped sample invoice failed validation.
   3. `tests/test_pdf_generator.py` had an unclosed parenthesis in its
      import statement, causing a `SyntaxError` that prevented pytest
      from collecting the file at all.

   At that point, only 16 of the suite's tests (`test_loader.py`,
   `test_renderer.py`) could be executed, because WeasyPrint requires
   native GTK/Pango/Cairo libraries that were not yet installed on the
   Windows machine used for verification.
3. **Current state (below):** the GTK3 runtime was installed on the
   verification machine (after an initial false start — see §1.1) and the
   **full suite was executed successfully: 57/57 tests passed.**

### 1.1 GTK Runtime Installation Note

The first install attempt (`choco install gtk-runtime`) installed a
**32-bit GTK2** runtime (2012-era, into `C:\Program Files (x86)\...`),
which failed to load into the 64-bit Python process with
`OSError: ... error 0xc1` (`ERROR_BAD_EXE_FORMAT`) — a hard architecture
mismatch, not a configuration issue. This was resolved by installing the
correct **64-bit GTK3 runtime** instead. This is recorded here since it is
a genuinely useful troubleshooting note for anyone re-running this project
on a fresh Windows machine.

## 2. Automated Test Suite (Unit + Integration)

### 2.1 Setup

```bash
python -m venv .venv
source .venv/bin/activate      # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

Requires the 64-bit GTK3 runtime for WeasyPrint on Windows — see
https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows.

### 2.2 Run

```bash
pytest tests/ -v --cov=billing_cli --cov-report=term-missing
```

### 2.3 Actual Result (executed 2026-07-23) — FULL SUITE, ALL PASSING

```
================================================ test session starts ================================================
platform win32 -- Python 3.14.2, pytest-9.0.3, pluggy-1.6.0 -- C:\Users\UjjalSaha\AppData\Local\Programs\Python\Python314\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\UjjalSaha\Documents\Capstone Projects\GHCP Capstone Project_AI QE
configfile: pyproject.toml
plugins: anyio-4.13.0, asyncio-1.3.0, cov-7.1.0
collected 57 items

tests/test_cli.py::TestBuildArgParser::test_parses_required_positional_args PASSED                             [  1%]
tests/test_cli.py::TestBuildArgParser::test_parses_verbose_flag PASSED                                         [  3%]
tests/test_cli.py::TestMainHappyPath::test_success_prints_output_path_and_returns_zero PASSED                  [  5%]
tests/test_cli.py::TestMainHappyPath::test_verbose_flag_sets_debug_logging PASSED                              [  7%]
tests/test_cli.py::TestMainErrorHandling::test_billing_cli_error_prints_to_stderr_and_returns_one PASSED       [  8%]
tests/test_cli.py::TestMainErrorHandling::test_unexpected_exception_is_caught_by_safety_net PASSED             [ 10%]
tests/test_cli.py::TestMainErrorHandling::test_pipeline_stops_on_first_error_does_not_call_downstream PASSED   [ 12%]
tests/test_integration.py::TestEndToEndSuccess::test_full_pipeline_generates_real_pdf PASSED                   [ 14%]
tests/test_integration.py::TestEndToEndSuccess::test_output_directory_auto_created PASSED                      [ 15%]
tests/test_integration.py::TestEndToEndOutputHandling::test_does_not_overwrite_existing_output_file PASSED     [ 17%]
tests/test_integration.py::TestEndToEndFileErrors::test_missing_invoice_file_reports_distinct_error PASSED     [ 19%]
tests/test_integration.py::TestEndToEndFileErrors::test_missing_template_file_reports_distinct_error PASSED    [ 21%]
tests/test_integration.py::TestEndToEndFileErrors::test_malformed_json_reports_distinct_error PASSED           [ 22%]
tests/test_integration.py::TestEndToEndFileErrors::test_missing_required_field_reports_field_name PASSED       [ 24%]
tests/test_integration.py::TestEndToEndPerformance::test_pipeline_completes_under_five_seconds PASSED          [ 26%]
tests/test_loader.py::test_load_template_returns_file_contents PASSED                                          [ 28%]
tests/test_loader.py::test_load_template_accepts_string_path PASSED                                            [ 29%]
tests/test_loader.py::test_load_template_raises_missing_file_error_when_not_found PASSED                       [ 31%]
tests/test_loader.py::test_load_template_raises_missing_file_error_when_path_is_directory PASSED               [ 33%]
tests/test_loader.py::test_load_template_preserves_utf8_content PASSED                                         [ 35%]
tests/test_loader.py::test_load_invoice_returns_validated_data PASSED                                          [ 36%]
tests/test_loader.py::test_load_invoice_accepts_the_shipped_sample_data PASSED                                 [ 38%]
tests/test_loader.py::test_load_invoice_raises_missing_file_error_when_not_found PASSED                        [ 40%]
tests/test_loader.py::test_load_invoice_raises_invalid_json_error_on_malformed_json PASSED                     [ 42%]
tests/test_loader.py::test_load_invoice_raises_schema_validation_error_on_missing_field PASSED                 [ 43%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_accepts_safe_values[INV-001] PASSED                      [ 45%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_accepts_safe_values[inv_2026_001] PASSED                 [ 47%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_accepts_safe_values[ABC123] PASSED                       [ 49%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_accepts_safe_values[a] PASSED                            [ 50%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_accepts_safe_values[1] PASSED                            [ 52%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_accepts_safe_values[a-b_c-123] PASSED                    [ 54%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_rejects_unsafe_values[../../etc/passwd] PASSED           [ 56%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_rejects_unsafe_values[inv/001] PASSED                    [ 57%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_rejects_unsafe_values[inv 001] PASSED                    [ 59%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_rejects_unsafe_values[inv/../../secret] PASSED           [ 61%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_rejects_unsafe_values[inv;rm -rf] PASSED                 [ 63%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_rejects_unsafe_values[inv$001] PASSED                    [ 64%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_rejects_unsafe_values[inv.001] PASSED                    [ 66%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_rejects_unsafe_values[] PASSED                           [ 68%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_rejects_unsafe_values[..] PASSED                         [ 70%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_rejects_unsafe_values[/] PASSED                          [ 71%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_rejects_unsafe_values[inv\\001] PASSED                   [ 73%]
tests/test_pdf_generator.py::test_sanitize_invoice_id_error_message_includes_offending_value PASSED            [ 75%]
tests/test_pdf_generator.py::test_resolve_output_path_creates_output_dir PASSED                                [ 77%]
tests/test_pdf_generator.py::test_resolve_output_path_raises_on_unsafe_invoice_id PASSED                       [ 78%]
tests/test_pdf_generator.py::test_resolve_output_path_raises_if_pdf_already_exists PASSED                      [ 80%]
tests/test_pdf_generator.py::test_markdown_to_html_wraps_content_in_html_document PASSED                       [ 82%]
tests/test_pdf_generator.py::test_markdown_to_html_renders_tables PASSED                                       [ 84%]
tests/test_pdf_generator.py::test_generate_pdf_writes_valid_pdf_file PASSED                                    [ 85%]
tests/test_pdf_generator.py::test_generate_pdf_cleans_up_temp_file_on_failure PASSED                           [ 87%]
tests/test_pdf_generator.py::test_generate_pdf_blocks_remote_resource_fetch PASSED                             [ 89%]
tests/test_renderer.py::test_render_markdown_substitutes_all_fields PASSED                                     [ 91%]
tests/test_renderer.py::test_render_markdown_iterates_line_items PASSED                                        [ 92%]
tests/test_renderer.py::test_render_markdown_raises_on_invalid_syntax PASSED                                   [ 94%]
tests/test_renderer.py::test_render_markdown_raises_on_missing_field PASSED                                    [ 96%]
tests/test_renderer.py::test_render_markdown_blocks_ssti_attribute_access PASSED                                [ 98%]
tests/test_renderer.py::test_render_markdown_does_not_execute_shell_via_template PASSED                        [100%]

================================================== tests coverage ===================================================
__________________________________ coverage: platform win32, python 3.14.2-final-0 __________________________________

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

**Result: 57 passed, 0 failed, 90% line coverage.** This is the full,
authoritative test-suite result for the project — no tests remain
unexecuted or blocked.

### 2.4 Regression Verification of the Three Fixed Bugs

Each fix was verified using the standard regression-test technique: the bug
was temporarily reintroduced, the test suite was re-run to confirm it fails
in exactly the way originally reported, then the fix was restored and the
suite was re-run to confirm it passes.

- **Bug 1 (`MissingFileErrorS` typo):** reintroducing the typo caused
  `tests/test_loader.py` to fail at collection with
  `ImportError: cannot import name 'MissingFileErrorS' from 'billing_cli.exceptions'`
  — reproducing the exact reported failure. Restoring the fix returned the
  suite to green.
- **Bug 2 (schema mismatch, `items` vs `line_items`):** reintroducing the
  old `items`-based required-field tuple caused the regression test
  `test_load_invoice_accepts_the_shipped_sample_data` to fail with
  `SchemaValidationError: Error: Invalid data - field 'items' is required`
  when validating the real `samples/data.json` — reproducing the exact
  reported failure. Restoring the fix returned the suite to green.
- **Bug 3 (`test_pdf_generator.py` unclosed paren):** confirmed via
  `ast.parse` that the file no longer raises `SyntaxError`; subsequently
  confirmed by the full suite run above, in which all 24 tests in this
  file executed and passed, including the WeasyPrint-dependent
  `generate_pdf`/`markdown_to_html`/`resolve_output_path` tests.

New regression tests added to `tests/test_loader.py` to lock in bugs 1 and
2 going forward: `test_load_invoice_returns_validated_data`,
`test_load_invoice_accepts_the_shipped_sample_data`,
`test_load_invoice_raises_missing_file_error_when_not_found`,
`test_load_invoice_raises_invalid_json_error_on_malformed_json`,
`test_load_invoice_raises_schema_validation_error_on_missing_field`.

## 3. Manual End-to-End Content Quality Check

Per the brief's Step 7 requirement to verify "the final output document
(content quality check)", the following manual procedure should still be
run once, using the provided sample files, to visually confirm the PDF
output (the automated suite confirms the pipeline runs and produces a
valid PDF file, but does not visually inspect its rendered layout):

```bash
python -m billing_cli.cli samples/data.json samples/template.md --verbose
```

**Input:** `samples/data.json` (2 line items, client "Acme Corp",
invoice `INV-2026-0723`, total `2000.0`) and `samples/template.md`
(Markdown table template). Confirmed to load and pass schema validation
via `load_invoice()`, and confirmed end-to-end by the automated
integration suite (§2.3) to produce a real PDF (`test_full_pipeline_generates_real_pdf`).

**Expected console output:**
```
Invoice PDF generated: ./output/invoice_INV-2026-0723.pdf
```
with exit code `0`.

**Content quality checklist (manual visual inspection of the resulting PDF):**
- [ ] PDF opens without corruption and is A4-sized.
- [ ] Heading "Invoice INV-2026-0723" renders correctly.
- [ ] Client name "Acme Corp" and date "2026-07-23" appear correctly.
- [ ] Table renders both line items with correct quantities, unit prices, and line totals.
- [ ] Total amount "2000.0" appears, bolded, at the bottom.
- [ ] No unrendered Jinja2 syntax (e.g., stray `{{ }}` or `{% %}`) appears anywhere in the output.
- [ ] Re-running the same command a second time is refused with a clear "file already exists" error and exit code `1` (FR-6 verification).

**ACTION REQUIRED BEFORE FINAL SIGN-OFF:** run the command above, open the
resulting PDF, tick each box above, and attach/embed a screenshot or the
PDF itself as the actual evidence artifact. This is the one remaining item
in this document — everything else is real, executed, passing evidence.

## 4. Traceability

**57/57 automated tests pass with 90% coverage — the full suite, with no
remaining blocked or unexecuted tests.** This project's Step 7 ("Verify")
is **fully executed and evidentially confirmed for the automated test
layer**. Only the manual PDF visual-inspection checklist in §3 remains as
a follow-up before final sign-off.
