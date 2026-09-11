# Research and source map

**Research date:** 2026-09-06. **Audience:** Maria, a reusable MariaDB architecture and optimization agent. **Scope:** data/column types, schema integrity, keys/indexes, query execution, statistics, locking, DDL, InnoDB resources, logging, replication, durability, and recovery, with skill/Boost integration.

This library is an original synthesis of primary documentation and practical engineering decisions. Sources are linked next to the supported claims in each guide. It is not a frozen manual, an exhaustive reading of every MariaDB feature, or a promise that a recommendation fits an uninspected server. Specialized features remain accessible through the official documentation index.

## Dated release context

The official August 25, 2026 maintenance announcement lists MariaDB 12.3.3, 11.8.9, 11.4.13, and 10.11.19. It also records the end of community maintenance for 10.6. This is a dated research snapshot, not an instruction to upgrade every installation to the newest series. Check the actual community/enterprise support entitlement and current release notes before making an upgrade decision. [Maintenance announcement](https://mariadb.org/mariadb-server-12-3-11-8-11-4-and-10-11-q3-2026-maintenance-releases-and-goodbye-10-6/), [Release and support overview](https://mariadb.org/about/)

No running MariaDB server was connected to or benchmarked to create this agent. Version-sensitive advice must be checked against the user's actual server, edition, topology, and data. Boost publication was designed for the installed project's 2.7.0 interface; that is an integration observation, not a requirement that Maria use Laravel.

## Evidence ledger

All source families below were consulted on the research date. MariaDB's current pages often contain multiple release tabs and do not expose a reliable last-updated date. Access date, exact release gates, and linked release notes provide the freshness record. HTTP Markdown retrieval was used when the browsing tool could not decode MariaDB's `text/markdown` responses.

| Claim family | Primary evidence read | Confidence and remaining checks |
| --- | --- | --- |
| Column representation and correctness | Storage requirements; numeric overview, INT, DECIMAL; TIMESTAMP/DATETIME; VARCHAR; charset/collation; JSON/UUID; generated columns. Links in [types and schema](types-schema.md). | High for documented semantics. Verify actual SQL mode, range, charset, client conversion, and patch-specific behavior. |
| Physical keys and access paths | Primary/unique constraints, CREATE TABLE, foreign keys, index design, row formats, ignored indexes, partition restrictions. Links in [keys and indexes](keys-indexes.md). | High for constraints and limits; index benefit requires representative measurements. Cookbook's historical tuning heuristics are not treated as modern rules. |
| Execution and optimizer | EXPLAIN, ANALYZE FORMAT=JSON, ANALYZE TABLE, InnoDB statistics, sargable date/upper improvements, semijoins, CTE/derived-table optimization, windows, pagination. Links in [query guide](queries-optimizer.md). | High for execution boundaries; plans depend on exact version, data, statistics, parameters, and configuration. |
| Concurrency and schema rollout | Isolation/locking reads, metadata locks, InnoDB status/variables, online-DDL overview, ALTER TABLE, online COPY history, implicit commits, Galera schema methods. Links in [locks and DDL](locks-ddl.md). | High for failure/locking distinctions. Rehearse the exact operation; online eligibility and cluster behavior are not universal. |
| Server resource optimization | MariaDB memory allocation, buffer pool, InnoDB variables, redo, page flushing, thread pool, query cache. Links in [server guide](innodb-server.md). | High for resource mechanisms; no universal tuning values or benchmark improvements asserted. |
| Logs and measurements | Log overview, slow/general logs, rotation, Performance Schema digest/timer documentation, audit plugin overview. Links in [observability guide](logging-observability.md). | High for purposes and units. Verify instrumentation, permissions, collection interval, and overhead on target. |
| Architecture and recovery | Storage engines, replication, backups, PITR, InnoDB-based binlog, release/support information. Links in [recovery guide](architecture-recovery.md). | High for documented requirements. No backup restore or failover was performed during agent creation. |
| Agent skills and Boost | Official Laravel Boost documentation and pinned 2.7.0 installation/tool implementation; installed command help/source. Links in [tools guide](tools-skills.md). | High for this installed version. Publication and a future session's runtime catalog are separate checks. |

## Important discrepancies and boundaries

- MariaDB and MySQL diverge in JSON storage, optimizer syntax/features, query-cache support, ignored/invisible indexes, binlogging, and configuration history. MySQL evidence is not silently substituted.
- The index cookbook includes historical examples and limits. Use its foundational reasoning alongside current row-format, optimizer, and release documentation.
- Indexed virtual-column expression recognition is version dependent. Generated-column/FK restrictions have inconsistent wording across documentation sections; inspect the exact definition and reproduce on the target before promising support.
- The online-schema page's banner and the documented 11.2 introduction history differ. Use the release and operation-specific behavior; neither “COPY always blocks” nor “online never blocks” is encoded as a rule.
- InnoDB variable pages contain version-tab differences, including changing buffer-pool controls and snapshot-isolation behavior. Query actual values before relying on defaults.
- InnoDB-based binlogging in 12.3 changes traditional log/durability/backup assumptions. Detect the active format before writing a procedure.
- Some old documentation URLs respond with HTTP 200 and a “Page Not Found” body. Resolve moved pages through the [official index](https://mariadb.com/docs/llms.txt) and validate the content, not just the response status.

## Refresh and verification

Refresh the affected reference after a server, connector, framework, or topology change. Check current official release notes and exact installed behavior; attach a date and supporting URL for material updates. Revalidate local links and skill metadata, republish complete skill folders, and run a representative task to check whether Maria uses the intended references and handles uncertainties correctly.

The diagnostic SQL is a reviewed reference menu, not a tested migration or an unattended production collection script. Agent validation establishes instruction structure, research access, and publication; database correctness/performance claims require a real application and authorized test environment.

Research stopped once the requested optimization areas had primary evidence, consequential disagreements were bounded, and remaining questions depended on a specific server/workload. The on-demand documentation workflow covers further topics without embedding the entire manual.
