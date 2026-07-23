"""Unit tests for billing_cli.loader.load_template and load_invoice."""

import json
from pathlib import Path

import pytest

from billing_cli.exceptions import InvalidJSONError, MissingFileError, SchemaValidationError
from billing_cli.loader import load_invoice, load_template

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"

VALID_INVOICE = {
    "invoice_id": "INV-001",
    "date": "2026-07-23",
    "client_name": "Acme Corp",
    "line_items": [
        {"description": "Consulting", "quantity": 2, "unit_price": 100.0, "line_total": 200.0}
    ],
    "total_amount": 200.0,
}


def test_load_template_returns_file_contents(tmp_path):
    template_path = tmp_path / "template.md"
    template_path.write_text("# {{ invoice_id }}", encoding="utf-8")

    result = load_template(template_path)

    assert result == "# {{ invoice_id }}"


def test_load_template_accepts_string_path(tmp_path):
    template_path = tmp_path / "template.md"
    template_path.write_text("content", encoding="utf-8")

    result = load_template(str(template_path))

    assert result == "content"


def test_load_template_raises_missing_file_error_when_not_found(tmp_path):
    missing_path = tmp_path / "does_not_exist.md"

    with pytest.raises(MissingFileError):
        load_template(missing_path)


def test_load_template_raises_missing_file_error_when_path_is_directory(tmp_path):
    with pytest.raises(MissingFileError):
        load_template(tmp_path)


def test_load_template_preserves_utf8_content(tmp_path):
    template_path = tmp_path / "template.md"
    template_path.write_text("Client: Ünïcödé Çørp", encoding="utf-8")

    result = load_template(template_path)

    assert result == "Client: Ünïcödé Çørp"


def test_load_invoice_returns_validated_data(tmp_path):
    invoice_path = tmp_path / "data.json"
    invoice_path.write_text(json.dumps(VALID_INVOICE), encoding="utf-8")

    result = load_invoice(invoice_path)

    assert result == VALID_INVOICE


def test_load_invoice_accepts_the_shipped_sample_data():
    """Regression test: samples/data.json must validate against the real
    schema used by requirements.md/README.md/architecture.md (line_items,
    total_amount), not the divergent 'items' schema that used to live in
    validator.py.
    """
    result = load_invoice(SAMPLES_DIR / "data.json")

    assert "line_items" in result
    assert "total_amount" in result


def test_load_invoice_raises_missing_file_error_when_not_found(tmp_path):
    missing_path = tmp_path / "does_not_exist.json"

    with pytest.raises(MissingFileError):
        load_invoice(missing_path)


def test_load_invoice_raises_invalid_json_error_on_malformed_json(tmp_path):
    invoice_path = tmp_path / "data.json"
    invoice_path.write_text("{not valid json,,,", encoding="utf-8")

    with pytest.raises(InvalidJSONError):
        load_invoice(invoice_path)


def test_load_invoice_raises_schema_validation_error_on_missing_field(tmp_path):
    bad_invoice = dict(VALID_INVOICE)
    del bad_invoice["client_name"]
    invoice_path = tmp_path / "data.json"
    invoice_path.write_text(json.dumps(bad_invoice), encoding="utf-8")

    with pytest.raises(SchemaValidationError):
        load_invoice(invoice_path)
