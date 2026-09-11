# Logging and observability

## Use the signal that answers the question

Error logs describe server health; slow logs identify expensive statements; the general log records received commands/connections; binary logs support replication/recovery. These have different purposes. A general-log record does not prove successful commit, and query timing alone does not explain application latency. [MariaDB logs](https://mariadb.com/docs/server/server-management/server-monitoring-logs/overview-of-mariadb-logs)

Prefer existing metrics and normalized statement digests before collecting raw query text. Rank by cumulative execution time and frequency, then examine average/tail behavior, rows examined/sent, temporary disk tables, and wait evidence. Check that Performance Schema, consumers, and relevant instruments are enabled. An empty table is not proof of no workload. A NULL digest can represent overflow when the digest table is full; account for reset/startup windows. [Statement digest summary](https://mariadb.com/docs/server/reference/system-tables/performance-schema/performance-schema-tables/performance-schema-events_statements_summary_by_digest-table)

Performance Schema statement timers use picoseconds; divide by `1e12` to express seconds. Keep count, sum, and average meanings distinct. Digests combine parameter values; inspect representative skew without exposing unnecessary literals. Snapshot differences are useful only when their counters refer to the same uninterrupted observation interval. [Statement history timer fields](https://mariadb.com/docs/server/reference/system-tables/performance-schema/performance-schema-tables/performance-schema-events_statements_history_long-table)

## Slow-query logging

Inspect existing enablement, destination, threshold, filters, sampling, and verbosity first. MariaDB 10.11 introduces names such as `log_slow_query`, `log_slow_query_time`, and `log_slow_min_examined_row_limit`; discover which names/aliases exist on the target. Thresholds can be session-scoped, so a global change may not alter established application sessions.

Logging every non-indexed query can generate noise from cheap scans. Combine intent with row/time filters, and account for sampling when interpreting volume. Plan/engine verbosity can help diagnosis but adds overhead and has version/output-destination restrictions. Size retention and rotation before increasing volume; raw SQL may contain sensitive business or personal data. Keep capture bounded and restore original settings after a temporary diagnostic window. [Slow query log](https://mariadb.com/docs/server/server-management/server-monitoring-logs/slow-query-log/slow-query-log-overview)

## General and audit logs

Use the general log selectively when a specific question requires commands as received, such as prepared-statement traffic. It grows quickly and records requests before outcomes are known. Capture the original global settings and output destinations, bound the window, and restore them on completion/error. Do not erase existing logs or switch shared output destinations merely to simplify a diagnostic query. [General query log](https://mariadb.com/docs/server/server-management/server-monitoring-logs/general-query-log)

When auditing is the requirement, inspect the installed audit plugin, supported events, destination, access control, retention, and overhead using the matching official plugin documentation. A performance trace is not automatically an audit system. [Audit plugin overview](https://mariadb.com/docs/server/reference/plugins/mariadb-audit-plugin/mariadb-audit-plugin-overview)

## Rotation and useful probes

Coordinate log rotation with the service's supported reopen/flush procedure and filesystem ownership. Confirm the new log actually receives entries and old files are released. Binary-log retention is separately coordinated with replicas and recovery; it is not ordinary file-log rotation. [Rotating logs](https://mariadb.com/docs/server/server-management/server-monitoring-logs/rotating-logs-on-unix-and-linux)

Build probes around bounded metadata or appropriately indexed predicates. A recurring unindexed COUNT over a huge table can create the apparent outage it claims to detect. Correlate server metrics with application/queue timing to find where latency accumulates. Use [diagnostic examples](diagnostics.sql) one section at a time; they deliberately do not enable logging, reset counters, or run analyzed application statements.

Treat InnoDB row counts and size metadata as estimates. Include system-versioned tables when inventorying stored data. `DATA_FREE` can describe free space in a shared tablespace rather than space uniquely reclaimable from that table; do not sum it into a promised saving. [Information Schema TABLES](https://mariadb.com/docs/server/reference/system-tables/information-schema/information-schema-tables/information-schema-tables-table)
