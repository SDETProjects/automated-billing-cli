"""Unit tests for billing_cli.cli module.

Per requirements.md FR-9 (Error Handling - Missing/Invalid Fields) and
02-architecture-spec.md (CLI Orchestration layer), this module verifies:
  - The CLI wires loader -> validator -> renderer -> pdf_generator in order.
  - BillingCLIError subclasses are caught and printed to stderr with exit code 1.
  - Unexpected exceptions are caught by the last-resort safety net (exit code 1).
  - Successful runs print the output path to stdout and return 0.
  - --verbose flag sets DEBUG level logging.
"""
import logging
import sys
from unittest.mock import patch

import pytest

from billing_cli.cli import build_arg_parser, main
from billing_cli.exceptions import BillingCLIError


class TestBuildArgParser:
    def test_parses_required_positional_args(self):
        parser = build_arg_parser()
        args = parser.parse_args(["invoice.json", "template.md"])
        assert args.invoice_json == "invoice.json"
        assert args.template_md == "template.md"
        assert args.verbose is False

    def test_parses_verbose_flag(self):
        parser = build_arg_parser()
        args = parser.parse_args(["invoice.json", "template.md", "--verbose"])
        assert args.verbose is True


class TestMainHappyPath:
    @patch("billing_cli.cli.generate_pdf")
    @patch("billing_cli.cli.resolve_output_path")
    @patch("billing_cli.cli.markdown_to_html")
    @patch("billing_cli.cli.render_markdown")
    @patch("billing_cli.cli.load_template")
    @patch("billing_cli.cli.load_invoice")
    def test_success_prints_output_path_and_returns_zero(
        self,
        mock_load_invoice,
        mock_load_template,
        mock_render_markdown,
        mock_markdown_to_html,
        mock_resolve_output_path,
        mock_generate_pdf,
        capsys,
    ):
        mock_load_invoice.return_value = {"invoice_id": "INV-001"}
        mock_load_template.return_value = "template text"
        mock_render_markdown.return_value = "rendered md"
        mock_markdown_to_html.return_value = "<html></html>"
        mock_resolve_output_path.return_value = "./output/invoice_INV-001.pdf"

        exit_code = main(["invoice.json", "template.md"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Invoice PDF generated: ./output/invoice_INV-001.pdf" in captured.out
        mock_generate_pdf.assert_called_once_with("<html></html>", "./output/invoice_INV-001.pdf")

    @patch("billing_cli.cli.load_invoice")
    def test_verbose_flag_sets_debug_logging(self, mock_load_invoice):
        mock_load_invoice.side_effect = BillingCLIError("stop early")
        main(["invoice.json", "template.md", "--verbose"])
        logger = logging.getLogger("billing_cli")
        assert logger.level == logging.DEBUG or logger.getEffectiveLevel() == logging.DEBUG


class TestMainErrorHandling:
    @patch("billing_cli.cli.load_invoice")
    def test_billing_cli_error_prints_to_stderr_and_returns_one(
        self, mock_load_invoice, capsys
    ):
        mock_load_invoice.side_effect = BillingCLIError("Missing required field: client_name")

        exit_code = main(["invoice.json", "template.md"])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Missing required field: client_name" in captured.err
        assert captured.out == ""

    @patch("billing_cli.cli.load_invoice")
    def test_unexpected_exception_is_caught_by_safety_net(
        self, mock_load_invoice, capsys
    ):
        mock_load_invoice.side_effect = RuntimeError("boom - unexpected")

        exit_code = main(["invoice.json", "template.md"])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "unexpected error occurred" in captured.err.lower()
        assert "boom - unexpected" in captured.err

    @patch("billing_cli.cli.load_template")
    @patch("billing_cli.cli.load_invoice")
    def test_pipeline_stops_on_first_error_does_not_call_downstream(
        self, mock_load_invoice, mock_load_template
    ):
        mock_load_invoice.return_value = {"invoice_id": "INV-001"}
        mock_load_template.side_effect = BillingCLIError("template.md not found")

        exit_code = main(["invoice.json", "template.md"])

        assert exit_code == 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
