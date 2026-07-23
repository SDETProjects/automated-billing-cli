"""Unit tests for billing_cli.renderer."""

import pytest

from billing_cli.renderer import TemplateRenderError, render_markdown


@pytest.fixture
def sample_invoice():
    """Return a minimal valid invoice dict for template rendering tests."""
    return {
        "invoice_id": "INV-001",
        "date": "2026-07-23",
        "client_name": "Acme Corp",
        "total_amount": 150.0,
        "line_items": [
            {"description": "Consulting", "quantity": 2, "unit_price": 75.0},
        ],
    }


def test_render_markdown_substitutes_all_fields(sample_invoice):
    template = (
        "# Invoice {{ invoice_id }}\n"
        "Client: {{ client_name }}\n"
        "Date: {{ date }}\n"
        "Total: {{ total_amount }}\n"
    )
    result = render_markdown(template, sample_invoice)
    assert "INV-001" in result
    assert "Acme Corp" in result
    assert "2026-07-23" in result
    assert "150.0" in result


def test_render_markdown_iterates_line_items(sample_invoice):
    template = (
        "{% for item in line_items %}"
        "{{ item.description }}: {{ item.quantity }} x {{ item.unit_price }}\n"
        "{% endfor %}"
    )
    result = render_markdown(template, sample_invoice)
    assert "Consulting: 2 x 75.0" in result


def test_render_markdown_raises_on_invalid_syntax(sample_invoice):
    broken_template = "{% for item in line_items %}{{ item.description }}"  # unclosed block
    with pytest.raises(TemplateRenderError):
        render_markdown(broken_template, sample_invoice)


def test_render_markdown_raises_on_missing_field(sample_invoice):
    template = "{{ nonexistent_field }}"
    with pytest.raises(TemplateRenderError):
        render_markdown(template, sample_invoice)


def test_render_markdown_blocks_ssti_attribute_access(sample_invoice):
    """Sandboxed environment must block access to dunder/internal attributes."""
    malicious_template = "{{ ''.__class__.__mro__[1].__subclasses__() }}"
    with pytest.raises(TemplateRenderError):
        render_markdown(malicious_template, sample_invoice)


def test_render_markdown_does_not_execute_shell_via_template(sample_invoice):
    """Guard against SSTI attempting OS command execution through the sandbox."""
    malicious_template = (
        "{{ self.__init__.__globals__.__builtins__.__import__('os').system('id') }}"
    )
    with pytest.raises(TemplateRenderError):
        render_markdown(malicious_template, sample_invoice)
