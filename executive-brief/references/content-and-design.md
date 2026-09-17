# Content and visual specification

Use the approved report as the composition source when available. The starter provides paper/forest/rust colors, serif editorial headings, opaque navigation, responsive panels, ECharts comparisons, an explorable architecture map, and cost controls. Demonstration data is never project evidence.

## Sections

1. Executive decision: operating state, purpose, proof, outstanding acceptance.
2. Architecture: edge/DNS/TLS, app, databases, cache, queues/workers, AI provider, artifacts/CDN, mail, payments, monitoring. Explain trust boundaries and data/control paths. Clickable nodes expose responsibility, dependencies, failures, evidence. Show actual topology.
3. Product journey: submit, capture, generate, review, publish, share/track, checkout, authorized delivery. Checkpoints, recovery, notifications.
4. Software inventory: installed versions, purpose, model/effort/limits, isolation, timeouts/retries, deployment mechanism.
5. Operations: CPU/RAM/disk/concurrency budgets, IAM/secrets, ingress, logs/redaction/retention, health, backup/restore proof, maintenance/restart behavior.
6. Acceptance: real end-to-end outcomes and failure classifications; distinguish browser, automated and infrastructure evidence. Preserve failed attempts and fixes as history.
7. Performance: phase timelines sharing a clock, completed durations, utilization versus capacity, queue versus provider waits. Label partial/resumed runs and noncomparable samples. Never graph ongoing jobs as completed.
8. Economics: adjustable assumptions, fixed compute/storage plus variable requests/egress/model usage; units/currency/region/date/pricing source/exclusions. Estimates are not bills; unknown prices stay unknown.
9. Growth: staged next steps tied to measured bottlenecks. Proposed hardware is distinct from provisioned hardware.
10. Sources/handoff: sanitized evidence, deployment/recovery/setup actions, blockers, print/download, immutable history.

## Visual behavior

- Editorial hero, concise status panels, charts before dense tables, details for raw numbers.
- ECharts global/axis/legend/tooltip text >=18px; readable textual fallbacks. Explicit units/domains. Separate CPU and RAM scales.
- Match project branding. Use official semantic Font Awesome icons. Never republish Pro assets in this public skill.
- Body/nav/forms/buttons20px, absolute minimum18px. Stack and wrap on mobile; never scale text down. Opaque sticky header, anchor offsets, reduced motion, visible focus.
- Cost controls update totals and charts; architecture nodes are keyboard buttons updating a detail panel. Charts resize with containers.
- Snapshot/edition visible. Dated additions explain superseded figures; retain historical narrative and evidence.
- Print retains decisions/evidence/assumptions/version while hiding controls. HTML downloads require companions unless explicitly bundled; don't promise a self-contained export.

## Dependencies

The starter references pinned ECharts6.0.0 from jsDelivr. For offline/private deployment, vendor the project's tested ECharts distribution with its Apache license/NOTICE, change to a relative script, and archive it. Never copy private embedded JSON merely to reuse styling.

Included icon paths are Font Awesome Free6 server, file-lines, print, download (CC BY4.0), attributed in the footer. Preserve attribution.
