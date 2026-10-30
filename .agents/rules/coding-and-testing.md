---
description: Coding guidelines, test requirements, database consistency, and verification discipline
always_on: true
---

# Coding and Testing Rules

1. **Modular Architecture**:
   - Clean layer separation: Models -> Schemas -> Repositories/Services -> Routers.
   - Decouple state transition business logic from HTTP request/response handlers.

2. **Database Integrity & Time Handling**:
   - Store all database timestamps as UTC timezone-aware values (`DateTime(timezone=True)`).
   - Use atomic transactions for multi-step mutations (e.g. advance stage + record audit log + recalculate stage due date).
   - Enforce database constraints: Foreign keys, Check constraints, and Unique indexes (e.g., deduplication key on notifications).

3. **Testing Expectations**:
   - Write automated pytest tests covering:
     * Valid and invalid workflow transitions.
     * Deficiency returns requiring mandatory remarks.
     * Separation of duties (institutions cannot verify undertakings).
     * Regional boundary isolation (cross-region queries denied).
     * Deadline calculation and deduplicated notification checks.
   - Run tests using the environment runner and verify zero regressions.

4. **Honest Reporting**:
   - Never report a feature as tested unless the test suite or browser interaction executed and passed.
   - Log any environment constraints or limitations explicitly.
