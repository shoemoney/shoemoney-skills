# Transactions, contention, and schema changes

## Diagnose the transaction, not just the waiting statement

Find the waiting statement, blocking transaction, transaction age, isolation level, touched indexes, and application transaction boundaries. A short statement inside a long transaction can hold resources for a long time. Check the actual session and global isolation settings; variable names and snapshot behavior differ across versions. Do not change isolation globally as an unexplained performance fix. [SET TRANSACTION](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/set-commands/set-transaction)

Use short transactions, consistent access order, selective indexed predicates, and bounded batches where semantics permit. A locking read needs an effective transaction context; `FOR UPDATE` does not provide a durable application-level lock after an autocommitted statement. Consider what happens between the read and write, including competing workers. [FOR UPDATE](https://mariadb.com/docs/server/reference/sql-statements/data-manipulation/selecting-data/for-update)

Metadata locks are distinct from InnoDB row locks. An open transaction can prevent DDL even when it is idle. Rolling back to a savepoint does not release its metadata locks. Inspect `lock_wait_timeout` separately from `innodb_lock_wait_timeout`. Performance Schema's `metadata_locks` table is available from 10.5.2, but instrumentation must be present and enabled to make missing rows meaningful. [Metadata locking](https://mariadb.com/docs/server/reference/sql-statements/transactions/metadata-locking)

## Classify failures before retrying

Deadlocks normally roll back a transaction. An InnoDB lock-wait timeout normally rolls back the statement; `innodb_rollback_on_timeout` changes that behavior. Do not retry the last statement blindly after either event. Have the application handle the transaction as a unit, preserve idempotency for external effects, and use bounded retry/backoff for genuinely retryable conflicts.

Check version-specific `innodb_snapshot_isolation` behavior as well: snapshot conflicts can produce error 1020 and require restarting the transaction. Verify whether the installed framework/driver recognizes that error as retryable. Never assume a Laravel retry parameter handles every MariaDB concurrency failure. [InnoDB variables](https://mariadb.com/docs/server/server-usage/storage-engines/innodb/innodb-system-variables)

Use `SHOW ENGINE INNODB STATUS` for transaction/lock context and its latest deadlock report; that report is not a history of every deadlock. Correlate it with timestamps and application failures. Broader deadlock logging is an intentional observability change with storage and sensitive-query implications. [InnoDB status](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/show/show-engine-innodb-status)

## Choose the actual DDL path

For each operation, identify table engine/format, MariaDB version, algorithm eligibility, table size, free temporary/data disk, write rate, metadata-lock blockers, replica effects, and recovery procedure. Rehearse with representative schema/data and concurrent traffic when operational execution is in scope.

`INPLACE` may rebuild the table; it does not mean instant. `NOCOPY` avoids a clustered-index rebuild, and `INSTANT` avoids changing data files for supported operations. `LOCK=NONE` permits concurrent DML during the eligible phase, but exclusive metadata-lock transitions still occur. Specify algorithm/lock requirements deliberately when a silent fallback would violate the rollout's constraints, and handle rejection as useful evidence. The old `alter_algorithm` system variable was removed in 11.5; use supported statement syntax. [InnoDB online DDL](https://mariadb.com/docs/server/server-usage/storage-engines/innodb/innodb-online-ddl/innodb-online-ddl-overview), [ALTER TABLE](https://mariadb.com/docs/server/reference/sql-statements/data-definition/alter/alter-table)

MariaDB 11.2 introduced online `COPY` for supported changes; a blanket claim that COPY always blocks writes is obsolete. Its change buffer can consume substantial disk under concurrent writes, and final synchronization still needs an exclusive lock. The online-schema page has a version banner that can conflict with its history; verify the exact release notes and operation instead of interpreting the banner as universal eligibility. [Online schema change](https://mariadb.com/docs/server/reference/sql-statements/data-definition/alter/alter-table/online-schema-change), [11.2 feature history](https://mariadb.com/docs/release-notes/community-server/old-releases/11.2/what-is-mariadb-112)

`ALTER TABLE` and `ANALYZE TABLE` cause implicit commits. Placing them inside a transaction does not create a rollback plan; implicit commit can occur even if the statement subsequently fails. Atomic DDL provides crash consistency for supported operations, not user rollback of a completed schema change. Cancellation can itself require lengthy rollback work. [Implicit commits](https://mariadb.com/docs/server/reference/sql-statements/transactions/sql-statements-that-cause-an-implicit-commit), [ALTER TABLE](https://mariadb.com/docs/server/reference/sql-statements/data-definition/alter/alter-table)

For narrowing columns or changing uniqueness/collation, validate existing data and future writes first. For incompatible application changes, prefer an explicit staged migration with compatible readers/writers, bounded backfill, validation, cutover, and a defined recovery path. Estimate costs; do not promise zero downtime without measuring the lock phases.

## Account for clustered topology

Galera schema changes need a cluster-wide plan. TOI preserves a common operation order but can block cluster work. RSU changes nodes locally and requires controlled mixed-schema compatibility and node-by-node execution. NBO is edition/version dependent; it does not mean target-table writes remain unrestricted. Check the installed provider and supported `wsrep_OSU_method` before choosing a method. [Galera schema upgrades](https://mariadb.com/docs/galera-cluster/galera-management/general-operations/performing-schema-upgrades-in-galera-cluster), [Galera variables](https://mariadb.com/docs/galera-cluster/reference/galera-cluster-system-variables)
