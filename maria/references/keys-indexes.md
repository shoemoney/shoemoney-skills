# Keys, indexes, and partitioning

## Keys define integrity and physical cost

InnoDB clusters rows by primary key and carries primary-key columns in secondary-index records. Prefer deliberate stable identity and account for key width across all secondary indexes. If no explicit PK exists, InnoDB can use an all-NOT-NULL unique index or a hidden identifier. Choose natural/composite versus surrogate identity based on access patterns and invariants, not a universal auto-increment rule. [Primary keys](https://mariadb.com/docs/server/architecture/server-constraints/primary-key-constraints)

A primary key is unique and non-null. UNIQUE permits multiple NULL values where the column is nullable; define nullability deliberately when uniqueness is a business invariant. `UNIQUE(a,b)` does not enforce `UNIQUE(a)`. A character-prefix unique index enforces prefix uniqueness, not full-value identity. [CREATE TABLE](https://mariadb.com/docs/server/server-usage/tables/create-table), [Unique constraints](https://mariadb.com/docs/server/architecture/server-constraints/unique-constraints-with-mariadb-enterprise-server)

Foreign keys require compatible column definitions and eligible indexes; integer size/sign and character charset/collation matter. A leading set of index columns is different from a truncated character-prefix index, which cannot support an FK. Check intended parent identity, child nullability, and cascade/restrict behavior. Composite child keys containing NULL can avoid requiring a matching parent. Cascades do not fire triggers. Partitioning and engine limitations apply. [Foreign keys](https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/optimization-and-indexes/foreign-keys)

Preserve CHECK/UNIQUE/FK enforcement when optimizing imports or schemas. Do not casually disable checks or assume reenabling them validates all prior rows. Inspect the relevant enforcement settings and verify invariants explicitly. [Constraints](https://mariadb.com/docs/server/reference/sql-statements/data-definition/constraint)

## Design indexes from a workload

Build a small candidate set around common predicates, joins, sorting/grouping, projection, and LIMIT behavior. Equality prefixes followed by a useful range/order are a starting hypothesis, not a fixed recipe. Composite column order determines which access paths exist. Low-cardinality columns can still be valuable inside a composite index or for a selective value.

Covering indexes can reduce base-row lookups; their width increases storage/cache and write costs. Character prefixes can improve filtering but cannot cover complete long values. Evaluate overlap across the workload and realistic data skew. The official index cookbook contains useful basic principles but also explicitly old examples; do not inherit its historic numeric cutoffs or blanket function/direction restrictions. [Index design cookbook](https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/optimization-and-indexes/building-the-best-index-for-a-given-select)

Index feasibility depends on row format, page size, character bytes, and type. For DYNAMIC/COMPRESSED, documented indexed-byte limits are 3072 with pages at least 16 KiB, 1536 with 8 KiB, and 768 with 4 KiB. Inspect the real configuration rather than assuming all tables use the same format. [Row formats and limits](https://mariadb.com/docs/server/server-usage/storage-engines/innodb/innodb-row-formats/innodb-row-formats-overview)

## Review candidates before removing indexes

A shorter nonunique index that matches a longer index's leading columns may be redundant, but verify uniqueness, FK support, truncated prefix lengths, sort directions, width, and actual access plans. A narrower index can still benefit some workloads. Zero observed reads are not proof of permanent non-use: account for restarts, instrumentation, rare reporting, and business cycles.

From MariaDB 10.6, an eligible index can be marked IGNORED to test optimizer avoidance while keeping it maintained. This does not measure savings from dropping its write maintenance. The explicit or implicit primary key cannot be ignored; hints naming an ignored index can error. Use MariaDB syntax and version-specific restrictions, not MySQL's INVISIBLE syntax. Validate the relevant workload before using this experiment. [Ignored indexes](https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/optimization-and-indexes/ignored-indexes)

Compare latency and rows examined for affected reads, insert/update/delete throughput, index/storage growth, memory pressure, and replication effects. Do not choose a drop solely from a shared first column or a fixed index-to-data-size ratio. Explain why each retained index exists.

Use actual index metadata, not names: inspect ordered columns, uniqueness, prefix lengths, type, and ignored state where supported. Cardinality is an estimate. [Information Schema STATISTICS](https://mariadb.com/docs/server/reference/system-tables/information-schema/information-schema-tables/information-schema-statistics-table)

## Partition only for a demonstrated purpose

Evaluate partitioning for retention, maintenance, and actual partition pruning. It is not automatic parallel query execution and does not replace indexes. All partition-expression columns must be included in every unique key; partitioned tables cannot have or be referenced by foreign keys. Those restrictions can change the data model's identity guarantees. Validate the exact partition scheme and query predicates. [Partitioning limitations](https://mariadb.com/docs/server/server-usage/partitioning-tables/partitioning-limitations)

For FULLTEXT, spatial, vector, or other specialized access, load the current feature reference and verify engine/version support, matching operator/index semantics, update cost, and measured retrieval quality. Do not treat them as ordinary BTREE indexes.
