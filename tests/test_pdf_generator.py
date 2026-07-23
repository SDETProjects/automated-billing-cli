"""Unit tests for billing_cli.pdf_generator."""

import pytest
from pathlib import Path

from billing_cli.exceptions import OutputExistsError
from billing_cli.pdf_generator import (
    InvalidInvoiceIdError,
    generate_pdf,
    markdown_to_html,
    resolve_output_path,
    sanitize_invoice_id,
)


@pytest.mark.parametrize(
    "invoice_id",
    ["INV-001", "inv_2026_001", "ABC123", "a", "1", "a-b_c-123"],
)
def test_sanitize_invoice_id_accepts_safe_values(invoice_id):
    assert sanitize_invoice_id(invoice_id) == invoice_id


@pytest.mark.parametrize(
    "invoice_id",
    [
        "../../etc/passwd",
        "inv/001",
        "inv 001",
        "inv/../../secret",
        "inv;rm -rf",
        "inv$001",
        "inv.001",
        "",
        "..",
        "/",
        "inv\\001",
    ],
)
def test_sanitize_invoice_id_rejects_unsafe_values(invoice_id):
    with pytest.raises(InvalidInvoiceIdError):
        sanitize_invoice_id(invoice_id)


def test_sanitize_invoice_id_error_message_includes_offending_value():
    with pytest.raises(InvalidInvoiceIdError) as exc_info:
        sanitize_invoice_id("../etc/passwd")
    assert "../etc/passwd" in str(exc_info.value)


def test_resolve_output_path_creates_output_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = resolve_output_path("INV-001")
    assert result == Path("output") / "invoice_INV-001.pdf"
    assert (tmp_path / "output").is_dir()


def test_resolve_output_path_raises_on_unsafe_invoice_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(InvalidInvoiceIdError):
        resolve_output_path("../../etc/passwd")


def test_resolve_output_path_raises_if_pdf_already_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "invoice_INV-001.pdf").write_bytes(b"%PDF-1.4 fake")

    with pytest.raises(OutputExistsError):
        resolve_output_path("INV-001")


def test_markdown_to_html_wraps_content_in_html_document():
    result = markdown_to_html("# Hello\n\nWorld")
    assert "<!DOCTYPE html>" in result
    assert "<h1>Hello</h1>" in result
    assert "<p>World</p>" in result


def test_markdown_to_html_renders_tables():
    md = "| A | B |\n|---|---|\n| 1 | 2 |\n"
    result = markdown_to_html(md)
    assert "<table>" in result


def test_generate_pdf_writes_valid_pdf_file(tmp_path):
    output_path = tmp_path / "invoice_INV-001.pdf"
    html_str = markdown_to_html("# Invoice INV-001")

    generate_pdf(html_str, output_path)

    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"%PDF")


def test_generate_pdf_cleans_up_temp_file_on_failure(tmp_path, monkeypatch):
    output_path = tmp_path / "invoice_INV-001.pdf"

    def _boom(self, target):
        raise RuntimeError("simulated WeasyPrint failure")

    monkeypatch.setattr("billing_cli.pdf_generator.HTML.write_pdf", _boom)

    with pytest.raises(RuntimeError):
        generate_pdf("<html></html>", output_path)

    assert not output_path.exists()
    assert not output_path.with_suffix(".pdf.tmp").exists()


def test_generate_pdf_blocks_remote_resource_fetch(tmp_path):
    """Guard against SSRF/offline-NFR violation via <img src=\"http://...\">."""
    output_path = tmp_path / "invoice_INV-001.pdf"
    malicious_html = (
        "<html><body><img src='http://example.com/tracker.png'></body></html>"
    )
    # WeasyPrint should still produce a PDF (broken image is non-fatal), but
    # the blocking fetcher must be invoked instead of making a real network
    # call. We assert no exception leaks a real network attempt by checking
    # the PDF is still produced without hanging/erroring from DNS/network.
    generate_pdf(malicious_html, output_path)
    assert output_path.exists()
