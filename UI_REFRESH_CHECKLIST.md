# SIH26262 UI Refresh Checklist

Status rule: `[x]` means confirmed from a source review or check actually run. `[ ]` means it still needs verification on the target computer.

## Changes applied

- [x] Replace the fake `AICTE` letter-block with a neutral product mark.
- [x] Clearly identify the product as an independent SIH26262 demonstration prototype.
- [x] Refresh the top navigation, profile, notifications and time display.
- [x] Refresh sidebar information hierarchy, navigation groups and active state.
- [x] Redesign login layout and demo role selector.
- [x] Improve shared cards, tables, form controls, buttons, badges and spacing.
- [x] Add responsive behavior for narrower screens.
- [x] Add keyboard-focus and reduced-motion support.
- [x] Simplify selected labels such as “Run SLA Sweep” to “Check deadlines”.
- [x] Update page title/description to identify a prototype instead of implying an official production portal.
- [x] Keep existing API calls and workflow behavior unchanged by design.
- [x] Keep `.env`, `node_modules`, generated `dist`, Python environments and runtime data out of the release ZIP.

## Verification still required

- [ ] `docker compose config -q` passes after placing the ZIP on the user's computer.
- [ ] `docker compose up --build` completes successfully on Windows.
- [ ] Frontend and backend containers report healthy.
- [ ] Login works for the existing local demo account.
- [ ] Dashboard loads live API data.
- [ ] Applications, case workbench, EVC, compliance, documents, alerts and audit screens render without console errors.
- [ ] Layout is checked at desktop and narrow/mobile widths.
- [ ] Main actions still work after the UI refresh.
- [ ] Keyboard navigation and form error states are checked.
- [ ] Existing security-review findings are handled before any non-local deployment.

## Build note

The TypeScript compiler completed without reporting errors in the available environment. The Vite bundler did not complete because the extracted Windows dependency tree lacked the Linux-specific Rollup optional dependency; a clean npm installation timed out. Therefore a frontend production build is **not marked as passed** here. Rebuild through Docker on the target Windows machine to verify the actual image.
