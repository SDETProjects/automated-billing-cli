"""Integration & E2E tests for the billing CLI pipeline.

Per requirements.md:
  - FR-5 (PDF Generation): valid JSON + template produces a real PDF.
  - FR-6 (Output File Handling): auto-creates ./output/, does not overwrite
    an existing file (exit code 1, "File already exists").
  - FR-7/FR-8 (Error Handling - Files): missing files and malformed JSON
    produce distinct error messages and exit code 1.
  - FR-10 (Success Output): prints "Invoice PDF generated: <path>" on success.

These tests exercise the REAL pipeline (loader -> validator -> renderer ->
pdf_generator) end-to-end via billing_cli.cli.main, using temp files instead
of mocks, per 02-architecture-spec.md's CLI orchestration contract.
"""
import json
from pathlib import Path

import pytest

from billing_cli.cli import main


VALID_INVOICE = {
    "invoice_id": "INV-E2E-001",
    "date": "2026-07-23",
    "client_name": "Acme Corp",
    "line_items": [
        {"description": "Consulting", "quantity": 2, "unit_price": 100.0, "line_total": 200.0}
    ],
    "total_amount": 200.0,
}

VALID_TEMPLATE = (
    "# Invoice {{ invoice_id }}\n\n"
    "**Client:** {{ client_name }}\n"
    "**Date:** {{ date }}\n\n"
    "| Description | Qty | Unit Price | Line Total |\n"
    "|---|---|---|---|\n"
    "{% for item in line_items %}| {{ item.description }} | {{ item.quantity }} "
    "| {{ item.unit_price }} | {{ item.line_total }} |\n{% endfor %}\n"
    "**Total: {{ total_amount }}**\n"
)


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    """Chdir into a temp directory so ./output/ is isolated per test."""
    monkeypatch.chdir(tmp_path)
    yield tmp_path


def write_invoice(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def write_template(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


class TestEndToEndSuccess:
    def test_full_pipeline_generates_real_pdf(self, workdir, capsys):
        invoice_path = workdir / "data.json"
        template_path = workdir / "template.md"
        write_invoice(invoice_path, VALID_INVOICE)
        write_template(template_path, VALID_TEMPLATE)

        exit_code = main([str(invoice_path), str(template_path)])

        assert exit_code == 0
        output_pdf = workdir / "output" / "invoice_INV-E2E-001.pdf"
        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0
        # PDF magic number check - real PDF, not a stub/text file.
        assert output_pdf.read_bytes()[:4] == b"%PDF"

        captured = capsys.readouterr()
        assert "Invoice PDF generated:" in captured.out

    def test_output_directory_auto_created(self, workdir):
        invoice_path = workdir / "data.json"
        template_path = workdir / "template.md"
        write_invoice(invoice_path, VALID_INVOICE)
        write_template(template_path, VALID_TEMPLATE)

        assert not (workdir / "output").exists()
        exit_code = main([str(invoice_path), str(template_path)])
        assert exit_code == 0
        assert (workdir / "output").is_dir()


class TestEndToEndOutputHandling:
    def test_does_not_overwrite_existing_output_file(self, workdir, capsys):
        invoice_path = workdir / "data.json"
        template_path = workdir / "template.md"
        write_invoice(invoice_path, VALID_INVOICE)
        write_template(template_path, VALID_TEMPLATE)

        first_exit = main([str(invoice_path), str(template_path)])
        assert first_exit == 0

        second_exit = main([str(invoice_path), str(template_path)])
        assert second_exit == 1
        captured = capsys.readouterr()
        assert "already exists" in captured.err.lower()


class TestEndToEndFileErrors:
    def test_missing_invoice_file_reports_distinct_error(self, workdir, capsys):
        template_path = workdir / "template.md"
        write_template(template_path, VALID_TEMPLATE)

        exit_code = main([str(workdir / "missing.json"), str(template_path)])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "missing.json" in captured.err
        assert captured.out == ""

    def test_missing_template_file_reports_distinct_error(self, workdir, capsys):
        invoice_path = workdir / "data.json"
        write_invoice(invoice_path, VALID_INVOICE)

        exit_code = main([str(invoice_path), str(workdir / "missing.md")])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "missing.md" in captured.err

    def test_malformed_json_reports_distinct_error(self, workdir, capsys):
        invoice_path = workdir / "data.json"
        template_path = workdir / "template.md"
        invoice_path.write_text("{not valid json,,,", encoding="utf-8")
        write_template(template_path, VALID_TEMPLATE)

        exit_code = main([str(invoice_path), str(template_path)])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "invalid json" in captured.err.lower() or "malformed" in captured.err.lower()

    def test_missing_required_field_reports_field_name(self, workdir, capsys):
        invoice_path = workdir / "data.json"
        template_path = workdir / "template.md"
        bad_invoice = dict(VALID_INVOICE)
        del bad_invoice["client_name"]
        write_invoice(invoice_path, bad_invoice)
        write_template(template_path, VALID_TEMPLATE)

        exit_code = main([str(invoice_path), str(template_path)])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "client_name" in captured.err


class TestEndToEndPerformance:
    def test_pipeline_completes_under_five_seconds(self, workdir):
        """Per Non-Functional Requirements: end-to-end execution under 5s."""
        import time

        invoice_path = workdir / "data.json"
        template_path = workdir / "template.md"
        write_invoice(invoice_path, VALID_INVOICE)
        write_template(template_path, VALID_TEMPLATE)

        start = time.monotonic()
        exit_code = main([str(invoice_path), str(template_path)])
        elapsed = time.monotonic() - start

        assert exit_code == 0
        assert elapsed < 5.0
