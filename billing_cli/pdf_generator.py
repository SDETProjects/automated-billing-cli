"""PDF generation for the Billing CLI (HARDENED per design-review).

Implements the sanitize_invoice_id -> resolve_output_path ->
markdown_to_html -> generate_pdf pipeline described in
docs/02-architecture-spec.md section 3.4.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import markdown as markdown_lib
from weasyprint import HTML

from billing_cli.exceptions import BillingCLIError, OutputExistsError

# Whitelist: only alphanumerics, underscore, and hyphen are permitted in
# an invoice_id once it is used to build a filesystem path. This closes
# the path-traversal risk (design-review SEC-3) where a malicious or
# malformed invoice_id like "../../etc/passwd" or "inv/00 1" could
# escape the intended ./output/ directory.
_SAFE_INVOICE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

OUTPUT_DIR = "output"

_HTML_STYLE = (
    "<style>"
    "@page { size: A4; margin: 2cm; }"
    "table { border-collapse: collapse; width: 100%; }"
    "table, th, td { border: 1px solid #333; padding: 6px; }"
    "</style>"
)


class InvalidInvoiceIdError(BillingCLIError):
    """Raised when invoice_id contains characters outside the safe whitelist."""

    def __init__(self, invoice_id: str):
        self.invoice_id = invoice_id
        super().__init__(
            f"Error: Invalid invoice_id '{invoice_id}' - only letters, digits, "
            "underscore, and hyphen are permitted."
        )


def sanitize_invoice_id(invoice_id: str) -> str:
    """Validate and return an invoice_id safe for use in a filesystem path.

    Per design-review SEC-3, the raw invoice_id from the (untrusted) input
    JSON file must never be used directly to build a filesystem path,
    since a value like "../../etc/passwd" could otherwise cause the
    generated PDF to be written outside ./output/ (path traversal).

    Args:
        invoice_id: The raw invoice_id string from the validated invoice data.

    Returns:
        The same invoice_id, unchanged, if it is already safe.

    Raises:
        InvalidInvoiceIdError: If invoice_id is empty or contains any
            character outside [A-Za-z0-9_-].
    """
    if not invoice_id or not _SAFE_INVOICE_ID_PATTERN.match(invoice_id):
        raise InvalidInvoiceIdError(invoice_id)
    return invoice_id


def resolve_output_path(invoice_id: str) -> Path:
    """Build the output PDF path for a given invoice_id.

    Per architecture spec section 3.4: builds ./output/invoice_<sanitized_id>.pdf;
    creates ./output/ via os.makedirs(exist_ok=True); raises OutputExistsError
    if the target PDF already exists (per REQ: never silently overwrite).

    Args:
        invoice_id: The RAW invoice_id (will be sanitized internally).

    Returns:
        The resolved Path to the target PDF file (not yet created).

    Raises:
        InvalidInvoiceIdError: If invoice_id fails sanitization.
        OutputExistsError: If a PDF already exists at the target path.
    """
    safe_id = sanitize_invoice_id(invoice_id)
    output_dir = Path(OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)
    output_path = output_dir / f"invoice_{safe_id}.pdf"
    if output_path.exists():
        raise OutputExistsError(str(output_path))
    return output_path


def markdown_to_html(md_text: str) -> str:
    """Convert Markdown (with the tables extension) into a full HTML document.

    Per architecture spec section 3.4: converts Markdown to an HTML fragment
    wrapped in a minimal HTML document with an inline <style> block sized
    for A4 pages with basic table borders.

    Args:
        md_text: The rendered Markdown document (from renderer.render_markdown).

    Returns:
        A complete HTML document string ready to hand to WeasyPrint.
    """
    html_fragment = markdown_lib.markdown(md_text, extensions=["tables"])
    return (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
        f"{_HTML_STYLE}</head><body>{html_fragment}</body></html>"
    )


def _blocking_fetcher(url: str):
    """WeasyPrint url_fetcher that blocks ALL remote/local resource resolution.

    Per design-review SEC-2 / architecture spec section 3.4: rejects all
    http(s):// and file:// resource resolution, enforcing the offline NFR
    so that no external network calls or local filesystem reads can be
    triggered by a malicious/malformed template embedding <img src=...> etc.
    """
    raise ValueError(f"Blocked network/file resource fetch (offline mode): {url}")


def generate_pdf(html_str: str, output_path: Path) -> None:
    """Render html_str to a PDF at output_path using an atomic write.

    Per architecture spec section 3.4 (design-review SEC-2, REL-1):
    configures WeasyPrint.HTML(string=html_str, url_fetcher=_blocking_fetcher)
    to guarantee the offline NFR, then writes to a temp file
    (<output_path>.tmp) first, atomically renaming it to output_path via
    os.replace() only after a fully successful write; on any exception,
    the temp file is deleted so no partial/corrupt PDF is ever left behind.

    Args:
        html_str: The full HTML document (from markdown_to_html).
        output_path: The resolved target Path (from resolve_output_path).

    Raises:
        Exception: Re-raises any WeasyPrint rendering or I/O error after
            cleaning up the temp file; callers (cli.py) are responsible for
            catching and translating this into a user-facing message.
    """
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        HTML(string=html_str, url_fetcher=_blocking_fetcher).write_pdf(str(tmp_path))
        os.replace(tmp_path, output_path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise
