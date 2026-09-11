# Query plans and optimization

## Start with evidence

Keep the SQL, bindings/distribution, schema/indexes, row estimates, server version, SQL mode, and workload concurrency together. Use `EXPLAIN FORMAT=JSON` for estimates or SHOW EXPLAIN/EXPLAIN FOR CONNECTION for an executing statement. EXPLAIN does not execute the requested SELECT/UPDATE/DELETE but can still acquire metadata locks. Inspect access paths, join order, estimated rows/filtering, sort/materialization, and output cardinality. [EXPLAIN](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/analyze-and-explain-statements/explain)

`ANALYZE FORMAT=JSON` **executes** the statement. Run it only when executing that statement is within scope and its load/effects are acceptable. `r_rows` is an average per execution; combine it with `r_loops` to understand repeated work. Parent `r_total_time_ms` includes children, so summing all node times double-counts. DML runtime excludes commit time. Engine counters are version-dependent and can be omitted when zero; missing I/O counters do not prove missing execution. [ANALYZE FORMAT=JSON](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/analyze-and-explain-statements/analyze-format-json)

A full scan can be cheaper than random lookups for a large result fraction. Filesort does not by itself mean disk sorting or failure. Compare actual work, query frequency, and service-level latency; avoid optimizing a plan label in isolation.

## Statistics are a separate mechanism

InnoDB persistent statistics survive restarts and can recalculate automatically based on data changes; sampling affects estimates. Verify table-specific settings when skew or estimated rows appear wrong. [InnoDB persistent statistics](https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/query-optimizations/statistics-for-optimizing-queries/innodb-persistent-statistics)

Engine-independent statistics use MariaDB syntax such as `ANALYZE TABLE ... PERSISTENT FOR COLUMNS (...) INDEXES (...)`; they do not automatically refresh in the same way. Collection can consume significant I/O, time, and storage. Target necessary columns/indexes, account for binary logging, and compare plans afterward. This command changes state and can implicitly commit; do not put it inside application transactions. Do not use MySQL's `UPDATE HISTOGRAM` syntax by assumption. [ANALYZE TABLE](https://mariadb.com/docs/server/reference/sql-statements/table-statements/analyze-table)

## Predicates and transformations

Bind values with matching types and avoid unintended conversions/collation changes. For time ranges, half-open bounds make precision and adjacent ranges explicit. Functions do not universally prevent index use: MariaDB 11.1+ can optimize qualifying DATE/YEAR comparisons, and 11.3+ supports certain UPPER/UCASE equality/IN forms under specific general_ci collations. Check the exact expression and actual plan; this is not blanket support for every function or collation. [DATE/YEAR sargability](https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/query-optimizations/sargable-date-and-year), [UPPER sargability](https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/query-optimizations/sargable-upper)

Eligible IN/EXISTS subqueries can receive semijoin or materialization optimizations. Replacing them with ordinary joins can multiply outer rows and change NULL semantics. Use the plan and result contract to select a form, rather than assuming joins always win. [Semijoin optimization](https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/query-optimizations/subquery-optimizations/semi-join-subquery-optimizations)

CTEs improve organization but do not guarantee cached or once-only computation. Inspect merge/materialization and predicate pushdown; grouping, DISTINCT, or windows can change available transformations. Do not apply a new-version optimizer hint to an older server. [Nonrecursive CTEs](https://mariadb.com/docs/server/reference/sql-statements/data-manipulation/selecting-data/common-table-expressions/non-recursive-common-table-expressions-overview), [Derived condition pushdown](https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/query-optimizations/optimizations-for-derived-tables/condition-pushdown-into-derived-table-optimization)

Window expressions run after WHERE/GROUP BY/HAVING; filter window results in an outer query. Specify ROWS/RANGE and tie behavior intentionally. A base-table index does not prove window processing avoids sorting. Inspect measured sorts and intermediate cardinality. [Window functions](https://mariadb.com/docs/server/reference/sql-functions/special-functions/window-functions/window-functions-overview)

## Page and batch without hidden unbounded work

Deep OFFSET locates and discards prior rows; concurrent changes can shift pages. For sequential large listings, consider keyset pagination using the full ordering tuple and a unique tiebreaker with an appropriate index. Preserve product requirements for arbitrary page jumps/totals instead of silently changing them. [Pagination optimization](https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/query-optimizations/pagination-optimization)

Bound batch sizes by measured lock/transaction/replication impact. Avoid changing the traversal key during processing. Investigate missing range bounds, repeated counts, N+1 calls, and polling amplification before adding indexes. Compare correctness, representative parameter sets, and read/write costs after each substantive rewrite.
