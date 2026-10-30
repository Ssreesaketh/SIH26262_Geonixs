---
description: UX/UI design guidelines for a credible Indian Government Administrative Operations Portal
always_on: true
---

# UX and UI Design Guidelines

1. **Aesthetic Direction**:
   - High-density, professional government-administration portal.
   - Color Palette:
     * Header & Primary Navigation: Deep Navy (`#0A2540` / `#0F172A`).
     * Backgrounds: Off-white / light slate neutral (`#F8FAFC`, `#F1F5F9`).
     * Accent & Action: AICTE Royal Blue (`#1D4ED8` / `#2563EB`) and subtle Teal.
     * Status Tones: Critical Overdue (Crimson `#DC2626`), Upcoming Warning (Amber `#D97706`), On-Track / Approved (Emerald `#059669`), Neutral Draft (Slate `#64748B`).
   - Restrained, crisp typography; clear table gridlines; accessible contrast ratios.

2. **Unified Product Trinity**:
   - **Control Tower**: Operational command center with real-time KPI metrics, stage-wise pendency charts, regional breakdown, and an overdue queue.
   - **Case Workbench**: Unified application processing screen with stage stepper, assigned official, contextual action buttons, documents, undertakings, EVC records, and chronological audit log.
   - **Compliance Radar**: Focused surveillance on expiring leases, time-bound undertakings, pending verification, and overdue SLA warnings.

3. **Interaction & State Discipline**:
   - Zero hardcoded mock metrics in React. Every count, card, and row originates from `/api/v1/dashboard/*` or application endpoints.
   - Explicit state rendering: Skeleton/spinner for Loading, friendly Empty states with guidance, detailed Error boundaries, and explicit Permission-Denied indicators with reasons.
   - Clear distinction between workflow progress (procedural step) and statutory decision (committee outcome).
