# Research and source map

**Research date:** 2026-09-06. **Audience:** Taytay, a reusable coding agent implementing and reviewing Laravel applications. **Scope:** practical decisions across Eloquent, data integrity/performance, queues and messaging, Octane, Reverb, Redis/PhpRedis, and Boost skill management. The companion framework map supports on-demand lookup across the rest of Laravel.

The guidance is an original synthesis of official Laravel/PHP/Redis documentation and implementation source, with engineering recommendations separated from framework guarantees. It is not a frozen copy of the manuals or a promise of permanent freshness. Links in each reference sit next to the claims they support.

## Version baseline and limitations

Laravel 13 is the current major documented during this research and requires PHP 8.3+. New capabilities include expanded PHP attributes, queue routing, JSON:API resources, and vector search. Existing applications still need their own exact compatibility check. Laravel's minor/patch release cadence means a major-version page can describe APIs absent from an earlier minor. [Laravel releases](https://laravel.com/docs/13.x/releases)

The project used to verify integration had locked and installed Laravel 13.30.1, Boost 2.7.0, Reverb 1.11.1, and Predis 3.6.0. Those are observations of that checkout, not requirements for Taytay or a claim that every package is the newest release. Octane and Horizon were not installed there; their guidance was researched from official documentation rather than tested as running services.

Minimum minor versions were not established for every recently added API. Taytay must inspect the installed implementation before adopting debounce/dispatch hooks, new attributes, pooled/direct database configuration, or new DDL/vector capabilities. PhpRedis extension support also depends on the actual runtime build.

## Evidence ledger

All documentation below is first-party, accessed on the research date. Documentation pages generally do not show a publication/update date, so the access date and version path are the freshness record. The linked upstream source branches move; Boost source links in its reference are pinned to v2.7.0 and were also checked against local installed source.

| Claim family | Supporting evidence and access notes | Confidence / remaining check |
| --- | --- | --- |
| Eloquent query shape, iteration, model lifecycle | Official Eloquent, relationships, database, queries, pagination, migrations, casts, and upgrade chapters; framework Model.php. Links in [Eloquent reference](eloquent-database.md). Relevant sections read. | High for observed behavior; verify exact runtime/engine and recent APIs. |
| Jobs and failure semantics | Laravel 12 and 13 queues, Horizon, FailoverQueue, BackgroundQueue, CallQueuedHandler, PendingDispatch. Links in [jobs reference](jobs-queues.md). Docs and implementation paths read. | High; failover consumption and debounce missing-key behavior corroborated in source. No universal exactly-once guarantee. |
| Event/notification/broadcast boundaries | Official events, notifications, broadcasting, Reverb chapters. Links in [real-time reference](events-realtime.md). Relevant sections read. | High; real transport delivery still needs application testing. |
| Worker lifetime and optimization | Official Octane, container, concurrency, deployment, Pulse. Links in [runtime reference](octane-runtime.md). | High; runtime choice and measured performance are application-specific. |
| Redis client/state behavior | Laravel Redis/cache, PhpRedis API/source, Redis Pub/Sub/eviction. Links in [Redis reference](redis-phpredis.md). | High; serializer/build/cluster details require runtime checks. |
| Boost skill discovery/publication | Official Boost docs plus installed 2.7.0 InstallCommand, UpdateCommand, SkillComposer, SkillWriter, Codex/Claude adapters, SearchDocs, tool registry, AddSkillCommand. Links in [Boost reference](boost-skills.md). | High for 2.7.0; inspect help and catalog for other versions. |
| Traits, scheduling, tests, API boundaries | PHP traits, Laravel scheduling, HTTP client, API resources, authorization, testing/database testing. Links in [toolbox](framework-toolbox.md). | High for covered rules; remaining chapter links are lookup targets. |

## Reconciled findings

- Current 12.x docs already include deferred/background queue connections and failover. Their presence does not establish an exact introduction release.
- Current 13.x relationships documentation includes opt-in automatic eager loading; it should not be omitted merely because a page-search match failed. Explicit loading and query measurements remain useful.
- Current query documentation includes MariaDB vector support as well as PostgreSQL; do not extrapolate an introductory release example into a complete engine-support matrix.
- Boost's moving documentation and installed 2.7.0 differ on default package discovery wording. Installed command help/source governs flags and behavior.
- Reverb's documentation includes a topology-specific port-capacity example. Actual capacity depends on process, proxy, network topology, OS, and workload; no universal inbound-client limit is encoded here.

## Refresh procedure

Re-run the project inventory after dependency/runtime changes. Use Boost search for the touched subsystem, then read official release/upgrade notes and installed source for consequential version-sensitive behavior. Update the affected reference and its provenance, publish through Boost, and test a representative task. Do not treat repeated secondary summaries as corroboration.

Research stopped when each requested specialist lane had primary evidence, important version discrepancies were resolved or bounded, and remaining uncertainty depended on a particular application's runtime or workload. The framework lookup map remains deliberately on demand rather than claiming exhaustive reading of every ecosystem manual.
