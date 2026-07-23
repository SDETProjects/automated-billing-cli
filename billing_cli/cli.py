"""Command-line entry point for the Automated Billing CLI.

Orchestrates the full pipeline per docs/02-architecture-spec.md section 4:
  load_invoice -> load_template -> render_markdown -> markdown_to_html
  -> resolve_output_path -> generate_pdf

Per FR-9: any error along the pipeline must print a single, distinct,
human-readable message to stderr and exit with code 1 - never a raw
Python traceback.
"""

from __future__ import annotations

import argparse
import logging
import sys

from billing_cli.exceptions import BillingCLIError
from billing_cli.loader import load_invoice, load_template
from billing_cli.logger import get_logger
from billing_cli.pdf_generator import generate_pdf, markdown_to_html, resolve_output_path
from billing_cli.renderer import render_markdown


def build_arg_parser() -> argparse.ArgumentParser:

    """Build the argparse parser for the billing CLI.

    Per requirements.md FR-1/FR-2: positional invoice_json path, positional
    template_md path, and an optional --verbose flag to enable DEBUG logging.
    """
    parser = argparse.ArgumentParser(
        prog="billing-cli",
        description="Generate a PDF invoice from a JSON data file and a Markdown template.",
    )
    parser.add_argument("invoice_json", help="Path to the invoice data JSON file.")
    parser.add_argument("template_md", help="Path to the Markdown/Jinja2 template file.")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG-level) logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the billing CLI pipeline end-to-end.

    Per FR-9: catches BillingCLIError (and its subclasses, covering every
    stage of the pipeline: loading, validation, rendering, and PDF
    generation) and any other unexpected exception, printing a single
    human-readable message to stderr and returning exit code 1. On
    success, prints the output PDF path to stdout and returns 0.
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    logger = get_logger()
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    try:
        logger.debug("Loading invoice data from %s", args.invoice_json)
        invoice_data = load_invoice(args.invoice_json)

        logger.debug("Loading template from %s", args.template_md)
        template_text = load_template(args.template_md)

        logger.debug("Rendering Markdown")
        rendered_markdown = render_markdown(template_text, invoice_data)

        logger.debug("Converting Markdown to HTML")
        html_str = markdown_to_html(rendered_markdown)

        logger.debug("Resolving output path for invoice_id=%s", invoice_data.get("invoice_id"))
        output_path = resolve_output_path(invoice_data["invoice_id"])

        logger.debug("Generating PDF at %s", output_path)
        generate_pdf(html_str, output_path)

    except BillingCLIError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - last-resort safety net per FR-9
        print(f"Error: An unexpected error occurred - {exc}", file=sys.stderr)
        return 1

    print(f"Invoice PDF generated: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
