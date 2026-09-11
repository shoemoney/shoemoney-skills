---
name: walk-the-funnel
description: >-
  End-to-end verification of user onboarding/conversion funnels by ACTUALLY WALKING them as a
  brand-new user — fresh plus-aliased email, programmatic inbox read, real browser, real prod.
  Use WHENEVER you ship or change anything that sends users down a path (auth gates whose error
  copy points at a signup/tokens page, onboarding flows, email verification, self-service key
  minting, payment/upgrade paths), WHENEVER error messages or docs tell users to "go do X" —
  verify X is actually reachable by the audience being sent there — and after ANY policy flip
  (public→auth, free→paid). The trigger smell: every component test is green, every piece was
  reviewed, and nobody has ever been a stranger in the system. Measured payoff: an auth gate
  whose 401 copy, FAQ, and five SDK READMEs all pointed at a /tokens page that returned 403 to
  every fresh signup — invisible to unit tests, code review, AND an adversarial review pass,
  found in 4 minutes of walking.
---

# Walk the funnel

Systems fail at the seams between correct components. The night this skill was written, every
piece of a new API auth gate was individually verified — middleware tests, live curl checks of
401/200 paths, an adversarial review — and the funnel was still broken end-to-end: the 401
message sent new users to a token page that a pre-existing members-only gate 403'd. No
component owned the whole path, so no component test could fail on it.

## The method

1. **Be an actual stranger.** Fresh account, not your admin/test user — allowlists and role
   flags on your usual accounts HIDE gates (an earlier CLI-login e2e passed only because the
   agent account was admin-allowlisted; the member gate never fired for it). Plus-aliasing
   (`you+probe1@domain`) gives unlimited fresh identities that deliver to an inbox you can
   read programmatically.
2. **Start where a stranger starts** — the error message, ad, or README that begins the
   funnel. Read it as instructions and follow them LITERALLY. Every link, every "go to X",
   every claimed default.
3. **Cross every seam in-band**: browser signup → email verify (read the inbox via API, click
   the real link) → the destination page → the thing it produces (a key, a session) → USE that
   artifact against the real service. The funnel is not walked until the final artifact
   produces the outcome the first message promised.
4. **Clean up**: revoke probe tokens (they end up in snapshot files on disk), note the probe
   account for later deletion. Verify revocation took (the key must actually stop working).

## What only this catches

- Gates from an earlier policy era still standing across a new funnel (the 403 above).
- Copy that references pages/flags/prices that drifted.
- Email deliverability + link signing + expiry in the real mail path.
- Ordering traps: verification required before a page the copy links directly.

## Pin it after fixing

Convert the walked path into a feature test where possible ("a token minted by a fresh
verified non-admin user passes the API auth middleware") — but know its limits: the in-repo
test can't see nginx, cached responses, or DNS. Re-walk the real funnel after any change to
its copy or its gates; four minutes is cheaper than a silent 100% conversion failure.
