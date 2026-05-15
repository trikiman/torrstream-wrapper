---
created: 2026-05-14T23:24:58.665Z
title: Fix slow theme toggle transition (1.4s vs 250ms)
area: ui
files:
  - templates/index.html:38-55
  - templates/index.html:667-672
---

## Problem

Clicking the theme button toggles `body.classList.toggle('light')` correctly
and the CSS variable `--bg` resolves to `#f5f5f5` immediately, but the actual
`backgroundColor` reaches the final light value at ~1.4s, not the declared
250ms.

Sampled timeline (E2E audit 2026-05-14):

```
  0 ms  rgb(13,13,13)        dark, before toggle
218 ms  rgb(155,155,155)
422 ms  rgb(202,202,202)
625-1231 ms  rgb(202,202,202)   stalls mid-transition
1432 ms rgb(245,245,245)        finally arrives at light
```

CSS in question (`templates/index.html`):

```css
:root { --bg: #0d0d0d; --transition: 0.25s cubic-bezier(.4,0,.2,1); ... }
.light { --bg: #f5f5f5; ... }
body { background: var(--bg); transition: background var(--transition), color var(--transition); }
```

The CSS reads correct on paper. Root cause is most likely one of:

1. CSS-variable-driven transitions are slower in Chrome because the browser
   has to recompute the variable cascade through every descendant before
   committing the new color, and we have a deep DOM (cards, modals, vidstack
   shadow trees).
2. Multiple ancestor elements also have `transition: ... var(--transition)`,
   and the cascade re-trigger pile-up extends total wall-clock time.
3. The `body` `transition` shorthand may be interfering with vidstack's own
   color transitions when the player overlay is active.

## Solution

Robust (no quick fix):

1. Switch theming to a single root attribute (`html[data-theme="light"]`)
   instead of a body class so the cascade root changes once. Removes any
   re-cascade-through-body overhead.
2. Apply transitions on a small, explicit set of properties at the elements
   that actually change color, NOT a global `body` rule that propagates to
   every descendant. E.g., `body { background-color: var(--bg); }` with the
   `transition` only set inside `@media (prefers-reduced-motion: no-preference)`.
3. Drop `var(--transition)` on `color` — text color barely changes in this
   theme, the perceived flicker isn't worth the extra reflow.
4. Verify by re-running the same sampling test from the audit; target ≤350ms
   total wall-clock to fully reach the target color.
5. Don't break the smooth-vs-snap aesthetic. Acceptable to clamp to a single
   `200ms ease-out`.

Verification hook: reuse the sampling JS from the E2E audit (capture
backgroundColor every 200ms while toggling .light) — bake it into a smoke
playbook entry.
