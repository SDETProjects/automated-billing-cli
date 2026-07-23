# Requirements: Automated Billing CLI (Invoice Generator)

## 1. Business Objective

Enable a freelance software engineer to automate the monthly billing process by generating professionally formatted PDF invoices from structured JSON billing data and a reusable Markdown/Jinja2 template, eliminating manual formatting effort while ensuring consistent, error-free output.

## 2. Functional Requirements

### FR-1: CLI Argument Acceptance
- **Given** the user runs the CLI tool
- **When** they provide a path to a `data.json` file and a path to a `template.md` file as arguments
- **Then** the system shall accept and parse both file paths for processing

### FR-2: JSON Schema Validation (Presence)
- **Given** a `data.json` file is provided
- **When** the system parses the file
- **Then** it shall validate that the following required fields are present: `invoice_id`, `date`, `client_name`, `line_items` (array), `total_amount`

### FR-3: JSON Schema Validation (Type)
- **Given** the required fields are present
- **When** the system validates the data
- **Then** it shall enforce the following types:
  - `invoice_id`: string or number
  - `date`: string
  - `client_name`: string
  - `line_items`: array of objects, each containing `description` (string), `quantity` (int), `unit_price` (float), `line_total` (float)
  - `total_amount`: float/number
- **Note:** Mathematical reconciliation of `line_items` totals against `total_amount` is explicitly out of scope for this version.

### FR-4: Template Merge
- **Given** valid JSON data and a Jinja2-syntax Markdown template (e.g., `{{ invoice_id }}`, `{{ client_name }}`)
- **When** the system processes the merge
- **Then** it shall render all top-level fields into the template and render `line_items` as a Markdown table (as defined by the template's own loop/table structure)

### FR-5: PDF Generation
- **Given** a successfully merged Markdown document
- **When** the system converts it to PDF
- **Then** it shall generate a PDF styled as standard A4, minimalist, with basic table borders, and no external CSS/branding

### FR-6: Output File Handling
- **Given** a generated PDF
- **When** the system saves the output
- **Then** it shall:
  - Auto-create the `./output/` directory if it does not exist
  - Save the file as `./output/invoice_<invoice_id>.pdf`
  - **If** a file with the same name already exists, **then** it shall NOT overwrite it; it shall print "File already exists" and exit with code `1`

### FR-7: Error Handling — Missing Files
- **Given** the `data.json` or `template.md` path does not exist
- **When** the CLI attempts to read the file
- **Then** it shall print a distinct, human-readable error message identifying which file is missing, and exit with code `1`

### FR-8: Error Handling — Malformed JSON
- **Given** the `data.json` file exists but contains invalid JSON syntax
- **When** the system attempts to parse it
- **Then** it shall print a distinct error message indicating malformed JSON, and exit with code `1`

### FR-9: Error Handling — Missing/Invalid Fields
- **Given** the JSON is syntactically valid but missing a required field or has an incorrect type
- **When** the system validates the schema
- **Then** it shall print a distinct error message naming the specific missing/invalid field, and exit with code `1`

### FR-10: Success Output
- **Given** the PDF is generated successfully
- **When** the process completes
- **Then** it shall print `Success: Generated [filepath]` to the console

### FR-11: Verbose Mode
- **Given** the `--verbose` flag is passed
- **When** the CLI executes
- **Then** it shall print additional debug output (e.g., parsed JSON schema) during execution

## 3. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Language/Runtime** | Python 3.10+ |
| **Offline Operation** | Must operate 100% offline; no external API calls for PDF rendering |
| **Performance** | End-to-end execution (parse → merge → render PDF) must complete in under 5 seconds |
| **Logging** | Console-only logging; `--verbose` flag enables debug-level output; default is minimal success/error messages |
| **Error Codes** | Standard exit code `1` for all failure modes; exit code `0` on success |
| **Reliability** | No partial/corrupt output files on failure (fail before writing, or clean up incomplete writes) |
| **Portability** | Must run cross-platform (Windows, macOS, Linux) given Python 3.10+ |
| **Security** | No hardcoded secrets/credentials; no execution of arbitrary code from JSON/template input |

## 4. Out of Scope

- Mathematical reconciliation/validation of `line_items` totals against `total_amount`
- Multi-currency support or locale-specific currency formatting
- Custom branding, logos, or external CSS styling in the PDF
- File overwrite/versioning support (e.g., auto-incrementing filenames)
- Network/API-based data sources (e.g., fetching billing data from a remote service)
- Authentication, multi-user, or SaaS-style deployment
- Automatic PDF file overwrite prompts or interactive confirmation

## 5. Clarification Trail (Copilot Q&A)

Per the Step 1 workflow, GitHub Copilot Chat was given the raw User Story
("build a tool that turns invoice data into a PDF bill") and asked to draft
requirements. Before finalizing, Copilot raised the following clarifying
questions; answers below were provided by the project owner and are
reflected in the FR/NFR sections above.

| # | Copilot's Clarifying Question | User's Answer | Requirement Impacted |
|---|---|---|---|
| 1 | Should the tool validate that `line_items` totals mathematically reconcile with `total_amount`? | No — out of scope for v1; trust the input data. | §4 Out of Scope |
| 2 | Should output support multiple currencies / locale-aware number formatting? | No — single currency, plain numeric formatting only. | §4 Out of Scope |
| 3 | Should the CLI overwrite an existing PDF if regenerated for the same invoice_id? | No — must refuse and exit with an error; user must delete/rename manually. | FR-6, §4 Out of Scope |
| 4 | Should the tool support fetching invoice data from a remote API instead of a local file? | No — 100% offline, local file input only. | NFR: Offline Operation |
| 5 | What should happen on malformed JSON vs. a JSON file that is missing a required field — same error or distinct? | Distinct, human-readable messages for each case; both exit code 1. | FR-9, FR-7/FR-8 |
| 6 | Should there be a `--verbose` / debug mode, and what should it output? | Yes — a `--verbose` flag that prints DEBUG-level logs (e.g., parsed schema, intermediate steps) without exposing secrets. | FR-11 |
| 7 | What is the acceptable end-to-end execution time budget? | Under 5 seconds for a typical single invoice. | NFR: Performance |
| 8 | Should custom branding/logos/CSS be supported in the generated PDF? | No — minimal, unstyled A4 layout only, for v1. | §4 Out of Scope |

These answers were incorporated directly into the Functional and
Non-Functional Requirements sections above before `architecture.md` was
drafted, satisfying the Step 1 requirement that Copilot's questions be
answered by the user prior to finalizing `requirements.md`.

