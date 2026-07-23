---
description: Execute the next phase or implementation task from the roadmap
targets: ['chat']
---

Read `#file:impl-plan.md` (task table T-1..T-17) and the current task ID provided by the user.

For the specified task:
1. Write TDD-style unit tests first, covering expected behavior and edge cases.
2. Generate the typed, enterprise-grade implementation code that satisfies those tests.
3. Follow the tech stack and module boundaries defined in `#file:docs/02-architecture-spec.md`.
4. Enforce the constraints and hardening rules in `#file:.github/copilot-instructions.md`.
5. Do not proceed to the next task until the user explicitly confirms this one is approved.

If the requested task is ambiguous or has unresolved dependencies on a prior task,
stop and ask for clarification instead of guessing.
