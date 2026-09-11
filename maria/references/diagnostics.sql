-- Maria's diagnostic menu. Select only relevant blocks; do not run as a batch.
-- Confirm target/environment/permissions and select the intended database first.
-- SELECT/SHOW can still impose load or reveal sensitive SQL. Metadata availability
-- and instrumentation vary by version. No settings or application data are changed.

-- 1. Server identity and selected database (client version is insufficient).
SELECT VERSION() AS server_version,
       @@version_comment AS server_build,
       DATABASE() AS selected_database;

-- 2. Current settings; nonexistent names are omitted, not reported as zero.
-- Inspect both GLOBAL and SESSION when evaluating connection-scoped behavior.
SHOW GLOBAL VARIABLES WHERE Variable_name IN (
    'version', 'version_comment', 'sql_mode', 'default_storage_engine',
    'character_set_server', 'collation_server', 'max_connections',
    'innodb_buffer_pool_size', 'innodb_page_size', 'innodb_default_row_format',
    'innodb_flush_log_at_trx_commit', 'sync_binlog', 'log_bin',
    'binlog_format', 'binlog_storage_engine', 'performance_schema',
    'slow_query_log', 'log_slow_query', 'long_query_time', 'log_slow_query_time',
    'log_output', 'general_log', 'tx_isolation', 'transaction_isolation',
    'innodb_snapshot_isolation', 'innodb_rollback_on_timeout',
    'innodb_lock_wait_timeout', 'lock_wait_timeout'
);

SHOW SESSION VARIABLES WHERE Variable_name IN (
    'sql_mode', 'autocommit', 'time_zone', 'character_set_connection',
    'collation_connection', 'tx_isolation', 'transaction_isolation',
    'long_query_time', 'log_slow_query_time',
    'innodb_lock_wait_timeout', 'lock_wait_timeout'
);

-- 3. Collect two snapshots with timestamps over a representative interval.
-- Use deltas for counters; detect restarts/resets. Some values are gauges.
-- Examples: buffer_pool_reads vs read_requests are counters; Threads_running
-- is a gauge. These alone do not establish latency, saturation, or root cause.
SELECT NOW(6) AS observed_at;
SHOW GLOBAL STATUS WHERE Variable_name IN (
    'Uptime', 'Questions', 'Threads_connected', 'Threads_running',
    'Connections', 'Max_used_connections', 'Aborted_connects',
    'Innodb_buffer_pool_read_requests', 'Innodb_buffer_pool_reads',
    'Innodb_buffer_pool_wait_free', 'Innodb_data_reads', 'Innodb_data_writes',
    'Innodb_os_log_written', 'Innodb_log_waits',
    'Innodb_row_lock_waits', 'Innodb_row_lock_time',
    'Created_tmp_tables', 'Created_tmp_disk_tables', 'Slow_queries'
);

-- 4. Approximate table footprint for the selected database.
-- A NULL DATABASE() produces no rows; that does not mean no tables exist.
-- InnoDB TABLE_ROWS and allocated sizes are estimates, not exact logical counts.
-- DATA_FREE may belong to a shared tablespace; do not sum it as reclaimable space.
-- Even metadata collection can be costly on large installations.
SELECT TABLE_NAME, TABLE_TYPE, ENGINE, ROW_FORMAT, TABLE_ROWS,
       DATA_LENGTH, INDEX_LENGTH, DATA_FREE, TABLE_COLLATION
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_TYPE IN ('BASE TABLE', 'SYSTEM VERSIONED')
ORDER BY COALESCE(DATA_LENGTH, 0) + COALESCE(INDEX_LENGTH, 0) DESC
LIMIT 30;

-- 5. For a chosen table, issue SHOW CREATE TABLE and SHOW INDEX with its actual,
-- correctly quoted identifier. Inspect constraints, key order, SUB_PART,
-- nullability, collation/direction, and engine/row format. Do not interpolate
-- untrusted identifiers or assume an index name proves its definition.

-- 6. Optional: normalized statement digests if Performance Schema is enabled
-- and this table/columns exist. Timers are picoseconds; /1e12 gives seconds.
-- Totals are since collection/reset, not automatically a recent window.
-- No rows can mean missing instrumentation, and NULL DIGEST can mean overflow.
-- Rank an interval by taking aligned snapshots outside this SQL when needed.
SELECT SCHEMA_NAME, DIGEST, LEFT(DIGEST_TEXT, 240) AS statement_pattern,
       COUNT_STAR,
       ROUND(SUM_TIMER_WAIT / 1000000000000, 3) AS total_seconds,
       ROUND(SUM_TIMER_WAIT / NULLIF(COUNT_STAR, 0) / 1000000000000, 6)
           AS average_seconds,
       SUM_ROWS_EXAMINED, SUM_ROWS_SENT,
       SUM_CREATED_TMP_DISK_TABLES
FROM performance_schema.events_statements_summary_by_digest
WHERE SCHEMA_NAME = DATABASE() OR DIGEST IS NULL
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 20;

-- 7. Optional contention snapshot; output can include query text.
-- The latest deadlock is not a complete deadlock history.
SHOW ENGINE INNODB STATUS;

-- EXPLAIN on a specific SELECT/UPDATE/DELETE is a separate estimated-plan step.
-- ANALYZE FORMAT=JSON executes its statement; ANALYZE TABLE changes statistics.
-- Do not substitute either into this read-only menu.
