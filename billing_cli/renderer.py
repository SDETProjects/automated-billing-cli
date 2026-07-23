"""Markdown rendering for the Billing CLI.

Merges validated invoice data into a Jinja2/Markdown template. Uses
jinja2.sandbox.SandboxedEnvironment (per architecture spec SEC-1) to
prevent template injection / SSTI, since template content originates
from a user-supplied file rather than a trusted, hardcoded source.
"""

from __future__ import annotations

from typing import Any

from jinja2 import StrictUndefined
from jinja2.exceptions import TemplateError
from jinja2.sandbox import SandboxedEnvironment

from billing_cli.exceptions import BillingCLIError


class TemplateRenderError(BillingCLIError):
    """Raised when the template cannot be parsed or rendered."""

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(f"Error: Template rendering failed - {detail}")


_env = SandboxedEnvironment(undefined=StrictUndefined, autoescape=False)


def render_markdown(template_text: str, invoice_data: dict[str, Any]) -> str:
    """Render a Markdown template against validated invoice data.

    Args:
        template_text: Raw Jinja2/Markdown template source (from load_template).
        invoice_data: Validated invoice dict (from load_invoice /
            validate_invoice_data). Top-level fields (invoice_id, date,
            client_name, total_amount) and the line_items list are made
            available to the template directly.

    Returns:
        The fully rendered Markdown document as a string.

    Raises:
        TemplateRenderError: If the template contains invalid Jinja2
            syntax, or if rendering fails for any other reason (e.g. a
            referenced field is missing from invoice_data).
    """
    try:
        template = _env.from_string(template_text)
        return template.render(**invoice_data)
    except TemplateError as exc:
        raise TemplateRenderError(str(exc)) from exc
    except TypeError as exc:
        # Raised if invoice_data contains keys that collide with
        # Python reserved keywords when spread as **kwargs.
        raise TemplateRenderError(str(exc)) from exc
