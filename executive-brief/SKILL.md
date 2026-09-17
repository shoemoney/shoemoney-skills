---
name: executive-brief
description: Create and maintain an interactive HTML executive briefing of a project's software, infrastructure, costs, operating evidence, risks, and roadmap, with immutable additive v+1 editions. Use for executive summaries, architecture handoffs, or briefing updates after material hardware/software changes.
---

# Executive Brief

Make the project understandable to its owner: what runs, how it connects, what it costs, what has actually passed, and how the system got here. Match the approved SiteRedo briefing's editorial layout and interactive depth. Produce `execbrief.html` with preserved version history; never replace a rich existing report with a shorter summary.

## Choose the starting point

- Existing briefing: inspect the latest **source**, published rendering, index, manifests, and publisher. Keep its layout, content, sections, charts, downloads, and evidence. Use the project's existing versioner when compatible; do not reset numbering or casually migrate its archive.
- New briefing: copy [assets/briefing.html](assets/briefing.html) and its adjacent assets into the document directory. Replace demonstration content with verified facts. Follow [references/content-and-design.md](references/content-and-design.md).
- SiteRedo: read [references/siteredo.md](references/siteredo.md); its established archive format differs from the portable helper.
- Automatic update: read [references/hooks.md](references/hooks.md). Detection nominates changes for review; it does not prove deployment or decide every edit deserves an edition.

## Evidence before narrative

Inspect the repository, installed versions, deployment manifests, and current infrastructure through authenticated tools. Record UTC observation time, environment, source/revision, and test scope. Separate **verified**, **configured but untested**, **in progress**, **historical**, and **proposed**. Missing metrics are unknown, never zero. Upgrades are capacity changes, not measured speedups. Do not claim business success from a test checkout or mail delivery from transport acceptance.

Keep credentials, user records, bearer URLs, private source archives, and raw logs out of public artifacts. Maintain the original audience and access controls. An unlinked URL and `noindex` are not access control. Publishing a reusable skill never authorizes publishing a project's private briefing or evidence.

## Build and version

1. Collect sanitized evidence; note what changed and why. Cover the sections in the design reference, retaining everything present.
2. Lead comparisons with ECharts and a clickable architecture infographic. Include source drilldowns, assumptions, and dates. Preserve 18px minimum text and 20px body text at every viewport, including chart labels/tooltips. Use actual semantic Font Awesome assets with license compliance.
3. Write a **dated additive body fragment** for an existing edition. Identify superseded historical facts without erasing them. New evidence filenames include an edition/date so earlier evidence stays pinned. Never reinterpret historical chart data using new defaults.
4. Use the native versioner, or the portable helper below. It starts v1, advances sequentially, chains source hashes, snapshots relative HTML/CSS dependencies, and preserves older files byte-for-byte. JavaScript-loaded assets and remote dependencies must be separately vendored/listed and verified; it does not crawl arbitrary JavaScript.

```sh
python3 <skill>/scripts/brief.py snapshot --source outputs/briefing.html --archive outputs/briefings --note 'Initial verified baseline'
python3 <skill>/scripts/brief.py snapshot --source outputs/briefing.html --archive outputs/briefings --addition outputs/update.html --note 'Worker migration and acceptance results'
python3 <skill>/scripts/brief.py verify --archive outputs/briefings
```

5. Test desktop/mobile rendering: computed text sizes, overflow, charts/tooltips, architecture selection, cost inputs, version/source links, print/download, keyboard focus, reduced motion, console errors. Test immutable history and companion paths. A passing build is not a browser check.
6. Publish through the established authorized path. For a new integration serve each immutable edition directory and assets; make `/execbrief.html` resolve to the latest `briefings/vN/index.html` with correct relative asset resolution (redirect is simplest). Add `/execbrief-vN.html` aliases if desired. Protect **all** edition/evidence routes. Atomically switch the latest pointer only after verifying uploaded hashes. No application/worker restart for a static report. The helper builds artifacts; it does not provide authentication or cloud deployment.
7. Verify the live authenticated page and unauthorized behavior. Acknowledge the change guard after documenting the result. Report version, URL, checks, and limitations concisely.

## Significant changes

Refresh after compute/storage/database/queue/topology migrations, framework/model/provider changes, major workflows, authentication/payments, security/recovery changes, material performance/cost findings, and acceptance milestones. Batch related work into one useful edition. Formatting-only edits and transient percentages usually do not merit one.

For cloud-console/CLI changes without watched repository edits, explicitly record:

```sh
python3 <skill>/scripts/change_guard.py mark --root <project> --note 'Changed worker capacity; verify live state'
```

A one-off document does not require hook installation. Do not turn ordinary invocation into unsolicited global automation.
