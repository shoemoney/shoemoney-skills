# InnoDB and server tuning

## Memory is a workload budget

Start with the effective host/container memory limit, other processes, resident memory, swap/OOM evidence, and active concurrency. Separate global caches, dynamic structures, per-connection allocations, and per-query buffers. `max_connections` is a limit rather than an immediate allocation, while multiple query operators can allocate buffers on demand. Do not treat either a simple maximum-buffer sum as exact usage or current idle usage as a safe peak. Leave measured headroom for bursts, temporary tables, maintenance, and the operating system. [MariaDB memory allocation](https://mariadb.com/docs/server/ha-and-performance/mariadb-memory-allocation)

Size the buffer pool against the active data/index working set and competing memory needs. Compare interval changes in logical read requests, physical reads, and free-page waits alongside disk latency. A high hit ratio does not rule out expensive scans or CPU work. Check actual resize capabilities and limits rather than copying a percentage of physical RAM. [InnoDB buffer pool](https://mariadb.com/docs/server/server-usage/storage-engines/innodb/innodb-buffer-pool)

Version-specific variables matter: `innodb_buffer_pool_instances` was ignored from 10.5.1 and removed in 10.6.0. Newer buffer-pool ceiling/shrink variables arrived in specific maintenance releases; query their actual values and platform support. Current prose contains differing default descriptions, so verify exact release behavior before assuming resizing bounds. Read back requested configuration changes and warnings. [InnoDB system variables](https://mariadb.com/docs/server/server-usage/storage-engines/innodb/innodb-system-variables)

## Redo and storage pressure

Relate redo generation, checkpoint progress, dirty pages, commit latency, and storage saturation. Larger redo capacity can reduce checkpoint pressure but affects recovery/storage planning. MariaDB uses one redo log from 10.5; `innodb_log_file_size` is dynamically adjustable from 10.9. Use the supported resize path; do not delete redo files as a tuning shortcut. [InnoDB redo log](https://mariadb.com/docs/server/server-usage/storage-engines/innodb/innodb-redo-log)

Set I/O capacity from sustainable observed storage behavior with headroom for foreground reads and log writes. `innodb_io_capacity` is not a universal cap on all disk activity: checkpoint, eviction, and emergency flushing differ. Monitor latency and dirty-page trends under load. Do not copy example NVMe IOPS settings onto shared or throttled storage. [Page flushing](https://mariadb.com/docs/server/server-usage/storage-engines/innodb/innodb-page-flushing)

## Concurrency and caches

More connections or workers can increase contention and tail latency. Evaluate application connection pooling and a bounded amount of active work. MariaDB's thread pool can help short CPU-bound OLTP workloads, but platform implementation, blocking work, queueing, and CPU quotas matter. Compare throughput and latency across a controlled concurrency sweep. [MariaDB thread pool](https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/buffers-caches-and-threads/thread-pool/thread-pool-in-mariadb)

MariaDB still has a query cache; do not import MySQL 8's removal as a MariaDB fact. It caches query results and can suffer invalidation/lock contention under writes and high concurrency. `SQL_NO_CACHE` bypasses that result cache, not the InnoDB buffer pool or OS cache. Distinguish cold-storage, warm-buffer, and cached-result measurements. [Query cache](https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/buffers-caches-and-threads/query-cache)

## Make changes interpretable

Record current values, source option files/managed settings, session versus global scope, whether existing connections inherit the change, and restart requirements. Change a coherent small set, measure a representative window, then retain or revert based on evidence. Diagnose transaction waits, bad query shapes, and saturation before treating a tuning variable as the cause. Use the [recovery reference](architecture-recovery.md) before changing commit durability or binary-log behavior.
