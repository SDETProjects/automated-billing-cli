# Design Review (v1 Draft — Superseded): Automated Billing CLI Architecture

> **Status: superseded.** This is the raw, first-pass Copilot review draft
> produced before the required changes below were verified as applied. The
> root-level `../design-review.md` is the polished, canonical Step 3
> deliverable and reflects the confirmed post-mitigation state (verdict:
> **APPROVED**, not the "CONDITIONALLY APPROVED" recorded below). This file
> is kept only for traceability of how the review evolved from v1 draft to
> the approved v2 record — treat `../design-review.md` as the source of
> truth for the design review outcome.

**Reviewer Role:** Brutal Senior Architecture Reviewer
**Subject:** `architecture.md` v1

## 1. Identified Risks

### 1.1 Security Risks

| ID | Risk | Severity | Detail |
|---|---|---|---|
| SEC-1 | Server-Side Template Injection (SSTI) | High | `renderer.py` uses a bare `Jinja2.Template(template_str).render()`. If a user ever runs this against a template.md received from a client or third party, arbitrary Jinja2 expressions (e.g., accessing `__class__.__mro__` to reach `os` via object introspection) could execute. The original 'trusted content' assumption is a loophole, not a control. |
| SEC-2 | Local File Disclosure / SSRF via WeasyPrint | High | WeasyPrint resolves `<img src="...">` and CSS `url()` references, including `file://` paths and remote HTTP(S) URLs, by default. This directly violates the "100% offline" NFR and could leak local files into the rendered PDF or make outbound network calls if the JSON/template contains a crafted image reference. |
| SEC-3 | Path Traversal via `invoice_id` | Medium | `invoice_id` is used directly to build the output filename (`invoice_<invoice_id>.pdf`). No sanitization is specified. A value like `../../etc/passwd` or containing path separators could write outside `./output/`. |
| SEC-4 | Unrestricted file read paths (CLI args) | Low | CLI accepts arbitrary file paths for `data.json`/`template.md` with no restriction to a working directory. Acceptable for a local single-user CLI, but worth explicitly documenting as an accepted risk rather than an oversight. |

### 1.2 Scalability Risks

| ID | Risk | Severity | Detail |
|---|---|---|---|
| SCALE-1 | Large `line_items` arrays | Low | No pagination or streaming; entire dataset is rendered in-memory. Acceptable given single-invoice CLI use case, but not documented as a bounded assumption. |

### 1.3 Maintainability / Reliability Risks

| ID | Risk | Severity | Detail |
|---|---|---|---|
| REL-1 | Non-atomic PDF write | High | `generate_pdf` writes directly to the final target path. A crash/interrupt mid-write leaves a corrupt, partial PDF at `invoice_<id>.pdf`. Because FR-6 forbids overwriting existing files, this corrupt file permanently blocks all future regeneration attempts for that invoice_id — a self-inflicted deadlock. |
| REL-2 | TOCTOU race on existence check | Low | `resolve_output_path` checks existence, then writes later. A concurrent/retried invocation could slip through. Low real-world impact for a single-user local CLI but must be documented as an accepted risk. |
| REL-3 | No encoding enforcement | Medium | No explicit UTF-8 enforcement when reading `data.json`/`template.md`, risking `UnicodeDecodeError` crashes (uncaught) or mangled output on non-ASCII client names. |

## 2. Missing NFRs

1. **Sandboxed template execution** — must specify use of `jinja2.sandbox.SandboxedEnvironment` instead of the default `Environment`/`Template`.
2. **Offline rendering enforcement** — must specify disabling remote/local resource fetching in WeasyPrint (custom `url_fetcher` that blocks all fetches, or restrict to `data:` URIs only).
3. **Filename sanitization** — must specify that `invoice_id` is sanitized (e.g., allow only `[A-Za-z0-9_-]`) before being used in a filesystem path.
4. **Explicit encoding** — must specify UTF-8 as the enforced read/write encoding for all file I/O.
5. **Atomic write guarantee** — must specify write-to-temp-then-rename pattern for PDF output.

## 3. Required Changes (Applied to architecture.md)

1. `renderer.py` updated to use `jinja2.sandbox.SandboxedEnvironment` instead of the default `Template` class (resolves SEC-1).
2. `pdf_generator.py` updated to configure WeasyPrint with a locked-down `url_fetcher` that rejects all external/local resource resolution, keeping rendering strictly offline (resolves SEC-2).
3. `pdf_generator.py` updated to sanitize `invoice_id` via a whitelist regex (`[^A-Za-z0-9_-]` stripped/rejected) before constructing the output path (resolves SEC-3).
4. `pdf_generator.py` updated to write PDF output to a temporary file in `./output/` and atomically `os.replace()` it to the final filename only after a successful write, with cleanup of the temp file on failure (resolves REL-1).
5. `validator.py` updated to explicitly open all files with `encoding="utf-8"` (resolves REL-3).
6. `architecture.md` §7 Assumptions updated to explicitly document TOCTOU race (REL-2), large-array memory assumption (SCALE-1), and unrestricted CLI file path access (SEC-4) as accepted risks for this local single-user CLI scope, rather than silent gaps.

## 4. Verdict

**Status: CONDITIONALLY APPROVED** — pending the 6 required changes above, which have been applied directly to `architecture.md` (see updated §3.3, §3.4, §7). No further architectural restructuring is required; the component boundaries and technology choices remain sound. Re-review not required unless implementation deviates from the patched design.
