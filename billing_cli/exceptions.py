"""Custom exception hierarchy for the Billing CLI.

Each exception carries a pre-formatted, human-readable message that
cli.py prints directly to the console before exiting with code 1.
"""


class BillingCLIError(Exception):
    """Base exception for all Billing CLI errors."""


class MissingFileError(BillingCLIError):
    """Raised when a required input file does not exist on disk."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Error: File not found - {path}")


class InvalidJSONError(BillingCLIError):
    """Raised when the data JSON file contains malformed JSON syntax."""

    def __init__(self, path: str, detail: str):
        self.path = path
        self.detail = detail
        super().__init__(f"Error: Invalid JSON in {path} - {detail}")


class SchemaValidationError(BillingCLIError):
    """Raised when required JSON fields are missing or have an invalid type."""

    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"Error: Invalid data - field '{field}' {reason}")


class OutputExistsError(BillingCLIError):
    """Raised when the target output PDF file already exists."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Error: File already exists - {path}")
