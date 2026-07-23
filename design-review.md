# Design Review: Automated Billing CLI Architecture

> Root-level deliverable for capstone SDLC Step 3 ("Design Review"). This
> mirrors and formalizes the risk register originally captured in
> `docs/00-evaluation-framework.md`, conducted with GitHub Copilot Chat
> acting as a senior/principal reviewer against `architecture.md` before any
> production code was written.

## 1. Review Method

Copilot Chat was given `architecture.md` (v1) and `requirements.md` and asked
to act as a Principal AI Architect / senior reviewer, specifically to:
1. Identify security, scalability, and reliability risks.
2. Flag any missing non-functional requirements (NFRs).
3. Recommend concrete changes before implementation began.

## 2. Identified Risks

### 2.1 Security Risks

| ID | Risk | Severity | Detail |
|---|---|---|---|
| SEC-1 | Server-Side Template Injection (SSTI) | High | Using the default Jinja2 `Environment`/`Template` on user-supplied template content allows arbitrary attribute access / code-adjacent introspection. |
| SEC-2 | Unrestricted remote resource fetching in PDF rendering | High | WeasyPrint's default `url_fetcher` will follow `http(s)://` and `file://` URIs referenced in the HTML/CSS, breaking the "100% offline" NFR and creating a data-exfiltration / SSRF-like vector. |
| SEC-3 | Path Traversal via `invoice_id` | Medium | `invoice_id` is used directly to build the output filename (`invoice_<invoice_id>.pdf`). No sanitization is specified. A value like `../../etc/passwd` or containing path separators could write output outside `./output/`. |
| SEC-4 | Unrestricted file read paths (CLI args) | Low | CLI accepts arbitrary file paths for `data.json`/`template.md` with no restriction to a working directory. Acceptable for a local single-user CLI, but worth explicitly documenting as an accepted risk rather than an oversight. |

### 2.2 Scalability Risks

| ID | Risk | Severity | Detail |
|---|---|---|---|
| SCALE-1 | Large `line_items` arrays | Low | No pagination or streaming; entire dataset is rendered in-memory. Acceptable given single-invoice CLI use case, but not documented as a bounded assumption. |

### 2.3 Maintainability / Reliability Risks

| ID | Risk | Severity | Detail |
|---|---|---|---|
| REL-1 | Non-atomic PDF write | High | `generate_pdf` writes directly to the final target path. A crash/interrupt mid-write leaves a corrupt, partial PDF at `invoice_<id>.pdf`. Because FR-6 forbids overwriting existing files, this corrupt file permanently blocks all future regeneration attempts for that `invoice_id` — a self-inflicted deadlock. |
| REL-2 | TOCTOU race on existence check | Low | `resolve_output_path` checks existence, then writes later. A concurrent/retried invocation could slip through. Low real-world impact for a single-user local CLI but must be documented as an accepted risk. |
| REL-3 | No encoding enforcement | Medium | No explicit UTF-8 enforcement on file reads for `data.json`/`template.md`, risking `UnicodeDecodeError` crashes (uncaught) or mangled output on non-ASCII invoice names. |

## 3. Missing NFRs (Flagged by Copilot)

1. **Sandboxed template execution** — must specify use of `jinja2.sandbox.SandboxedEnvironment` instead of the default `Environment`/`Template`.
2. **Offline rendering enforcement** — must specify disabling remote/local resource fetching in WeasyPrint (custom `url_fetcher` that blocks all fetches, or restricts to `data:` URIs only).
3. **Filename sanitization** — must specify that `invoice_id` is sanitized (e.g., allow only `[A-Za-z0-9_-]`) before being used in a filesystem path.
4. **Explicit encoding** — must specify UTF-8 as the enforced read/write encoding for all file I/O.
5. **Atomic write guarantee** — must specify write-to-temp-then-rename pattern for PDF output.

## 4. Design Decisions & Required Changes (Applied to architecture.md)

| Decision | Rationale |
|---|---|
| `renderer.py` updated to use `jinja2.sandbox.SandboxedEnvironment` instead of the default `Template` class | Resolves SEC-1. |
| `pdf_generator.py` updated to configure WeasyPrint with a locked-down `url_fetcher` that rejects all external/local resource resolution, keeping rendering strictly offline | Resolves SEC-2. |
| `pdf_generator.py` updated to sanitize `invoice_id` via a whitelist regex (`[^A-Za-z0-9_-]` stripped/rejected) before constructing the output path | Resolves SEC-3. |
| `pdf_generator.py` updated to write PDF output to a temporary file in `./output/` and atomically `os.replace()` it to the final filename only after a successful write, with cleanup of the temp file on failure | Resolves REL-1. |
| `validator.py`/`loader.py` updated to explicitly use `encoding="utf-8"` on all file reads | Resolves REL-3. |
| `architecture.md` §5/§6 updated to explicitly document the TOCTOU race (REL-2), large-array memory assumption (SCALE-1), and unrestricted CLI file path access (SEC-4) as accepted risks for this local, single-user scope, rather than silent gaps | Provides traceability; avoids "happy path" bias by making trade-offs explicit rather than omitted. |

## 5. Verdict

**Status: APPROVED** (post-mitigation). All 5 High/Medium-severity risks
(SEC-1, SEC-2, SEC-3, REL-1, REL-3) were mitigated via the changes above,
which were applied directly to `architecture.md` §3–§4 and implemented in
`billing_cli/renderer.py`, `billing_cli/pdf_generator.py`, and
`billing_cli/loader.py`. The two remaining Low-severity risks (REL-2 TOCTOU,
SEC-4 unrestricted CLI paths) and SCALE-1 are explicitly accepted as
reasonable trade-offs for a local, single-user, offline CLI and are carried
forward into `README.md` → "Out of Scope" and the PR's "Known Limitations"
section. No further architectural restructuring is required; component
boundaries and technology choices remain sound. Re-review is not required
unless implementation deviates materially from this reviewed design.

## 6. Sign-off

| Role | Reviewer | Outcome |
|---|---|---|
| Senior Reviewer (simulated) | GitHub Copilot Chat | Identified 8 risks, proposed 5 NFRs, recommended 6 concrete changes. |
| Human-in-the-loop | Project owner | Reviewed and approved all Copilot recommendations; authorized implementation to proceed (Step 4/5). |
