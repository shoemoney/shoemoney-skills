# SiteRedo adapter

The inspiration is the owner's authenticated `/execbrief.html`, not redistributable project data. The skill contains no private instance IDs, account numbers, buyer records, source ZIPs, or signed URLs.

Resolve the SiteRedo checkout from current project context. Inspect project-relative sources:

- `outputs/briefings/index.json`: latest edition and archive list.
- `outputs/briefings/vN/siteredo-executive-briefing.html`: full additive source.
- `outputs/briefings/vN/execbrief.html`: rendered edition.
- `outputs/briefings/vN/manifest.json`: file digests/prior source digest.
- `ops/version_briefing.py`, `ops/publish_briefings.py`, `ops/install_briefings.py`: native snapshot/publication.
- Controller and routes serving `/execbrief.html` and companions: verify actual admin middleware.
- `outputs/evidence/` and dated additions: provenance, sanitized for intended audience.

Do not run generic `brief.py` against this archive: source names/manifests differ. Keep native versioning and test preservation. Inspect companion copying: uniquely name new evidence and ensure historical bytes aren't refreshed from mutable working files.

```sh
python3 ops/version_briefing.py --addition outputs/briefing-vNEXT-addition.html --note 'Dated evidence-backed update'
python3 ops/publish_briefings.py
```

Read deployment/SSM results to completion. Verify current/old routes under admin authentication and signed-out rejection. No queue restart for static publication. Follow the project's command wrapper conventions.

Preserve all original sections and additions: software, architecture, workflow, isolation, backups/health/logs, performance, acceptance, adjustable costs, growth, sources, two-page homepage-first rule, checkout scope/consent, private operations, payment mode, login, worker migration/recovery, outreach readiness. Refresh factual status; this inventory is not proof of deployment.
