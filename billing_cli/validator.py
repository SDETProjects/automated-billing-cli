"""Validation utilities for the Billing CLI.

Provides typed, pure validation functions for invoice input data.
All validators raise SchemaValidationError (from billing_cli.exceptions)
on failure. No I/O or network access is performed here, consistent
with the offline-only constraint.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Mapping

from billing_cli.exceptions import SchemaValidationError

_INVOICE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_REQUIRED_INVOICE_FIELDS = ("invoice_id", "client_name", "date", "line_items", "total_amount")
_REQUIRED_ITEM_FIELDS = ("description", "quantity", "unit_price", "line_total")


def validate_invoice_id(invoice_id: str) -> None:
    """Validate that invoice_id is safe for use as a filename component."""
    if not isinstance(invoice_id, str) or not invoice_id:
        raise SchemaValidationError("invoice_id", "must be a non-empty string")
    if not _INVOICE_ID_PATTERN.match(invoice_id):
        raise SchemaValidationError(
            "invoice_id",
            "may only contain letters, digits, '_' and '-' (max 64 characters)",
        )


def validate_date(value: str) -> date:
    """Validate an ISO-8601 date string (YYYY-MM-DD) and return a date."""
    if not isinstance(value, str):
        raise SchemaValidationError("date", "must be a string in YYYY-MM-DD format")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SchemaValidationError(
            "date", f"'{value}' is not a valid YYYY-MM-DD date"
        ) from exc


def validate_non_empty_string(value: Any, field_name: str) -> str:
    """Validate that value is a non-empty, stripped string."""
    if not isinstance(value, str) or not value.strip():
        raise SchemaValidationError(field_name, "must be a non-empty string")
    return value.strip()


def validate_positive_number(value: Any, field_name: str) -> float:
    """Validate that value is a positive, finite number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemaValidationError(field_name, "must be a number")
    if value <= 0:
        raise SchemaValidationError(field_name, "must be greater than zero")
    return float(value)


def validate_item(item: Mapping[str, Any], index: int) -> None:
    """Validate a single invoice line item at index."""
    if not isinstance(item, Mapping):
        raise SchemaValidationError(f"line_items[{index}]", "must be an object")
    for field in _REQUIRED_ITEM_FIELDS:
        if field not in item:
            raise SchemaValidationError(f"line_items[{index}]", f"missing '{field}'")
    validate_non_empty_string(item["description"], f"line_items[{index}].description")
    validate_positive_number(item["quantity"], f"line_items[{index}].quantity")
    validate_positive_number(item["unit_price"], f"line_items[{index}].unit_price")
    validate_positive_number(item["line_total"], f"line_items[{index}].line_total")


def validate_invoice_data(data: Mapping[str, Any]) -> None:
    """Validate the full invoice payload loaded from JSON input."""
    if not isinstance(data, Mapping):
        raise SchemaValidationError("<root>", "invoice data must be a JSON object")

    for field in _REQUIRED_INVOICE_FIELDS:
        if field not in data:
            raise SchemaValidationError(field, "is required")

    validate_invoice_id(data["invoice_id"])
    validate_non_empty_string(data["client_name"], "client_name")
    validate_date(data["date"])

    line_items = data["line_items"]
    if not isinstance(line_items, list) or not line_items:
        raise SchemaValidationError("line_items", "must be a non-empty list")
    for index, item in enumerate(line_items):
        validate_item(item, index)

    validate_positive_number(data["total_amount"], "total_amount")
