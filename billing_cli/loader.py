"""Invoice data loading utilities for the Billing CLI.

Reads invoice JSON files from disk and validates their contents before
handing off a plain dict to the rendering layer. This is the only module
permitted to perform file I/O when reading invoice input; it never makes
network calls, keeping the CLI fully offline as per the architecture.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from billing_cli.exceptions import InvalidJSONError, MissingFileError
from billing_cli.validator import validate_invoice_data

_MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB guard against oversized input


def load_invoice(path: str | Path) -> dict[str, Any]:
    """Load, parse, and validate an invoice JSON file.

    Args:
        path: Filesystem path to the invoice JSON file.

    Returns:
        A validated dict representing the invoice payload.

    Raises:
        MissingFileError: If the file does not exist or is not a file.
        InvalidJSONError: If the file cannot be read or contains malformed
            JSON, or exceeds the maximum permitted size.
        SchemaValidationError: If the parsed data fails schema validation.
    """
    invoice_path = Path(path)

    if not invoice_path.exists() or not invoice_path.is_file():
        raise MissingFileError(str(invoice_path))

    try:
        size = invoice_path.stat().st_size
    except OSError as exc:
        raise InvalidJSONError(str(invoice_path), f"could not stat file: {exc}")
    if size > _MAX_FILE_SIZE_BYTES:
        raise InvalidJSONError(
            str(invoice_path),
            f"file exceeds the {_MAX_FILE_SIZE_BYTES} byte size limit",
        )

    try:
        raw_text = invoice_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise InvalidJSONError(str(invoice_path), f"could not read file: {exc}")

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise InvalidJSONError(str(invoice_path), str(exc))

    # Let SchemaValidationError propagate as-is; it is a distinct, more
    # specific failure mode than a load/parse failure and callers may
    # wish to handle the two differently.
    validate_invoice_data(data)

    return data


def load_template(path: str | Path) -> str:
    """Load a Jinja2/Markdown template file from disk.

    Args:
        path: Filesystem path to the template.md file.

    Returns:
        The raw template text as a string.

    Raises:
        MissingFileError: If the file does not exist or is not a file.
        InvalidJSONError: If the file cannot be read due to an OS or
            encoding error. (Reused here as the generic "unreadable
            input file" error per the exception hierarchy; the message
            clarifies this is a template, not JSON, read failure.)
    """
    template_path = Path(path)

    if not template_path.exists() or not template_path.is_file():
        raise MissingFileError(str(template_path))

    try:
        return template_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise InvalidJSONError(str(template_path), f"could not read file: {exc}") from exc
