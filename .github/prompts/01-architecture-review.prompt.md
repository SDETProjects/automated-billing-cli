---
description: Perform a brutal technical due-diligence review of the proposal
targets: ['chat']
---

Read `#file:requirements.md` and `#file:docs/02-architecture-spec.md`.

Execute the review process defined in `#file:design-review.md` (canonical
Step 3 record; `#file:docs/00-evaluation-framework.md` is the superseded v1
draft, kept for traceability only).
Provide a brutal, unvarnished architectural review before writing any production code.

Flag any of the following if present:
- Non-deterministic AI usage where deterministic logic or regex would suffice.
- Missing input sanitization, secret management, or offline-constraint violations.
- Missing test coverage plans for any proposed module.
- Ambiguous requirements that should block progress to the design phase.
