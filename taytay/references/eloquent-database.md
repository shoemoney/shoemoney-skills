# Eloquent and database engineering

## Design the query from the required result

Choose only needed columns while retaining IDs and relationship keys. Use constrained `with`, `withWhereHas`, `loadMissing`, and polymorphic `morphWith`/`loadMorph` where appropriate. Prefer `withCount`, `withExists`, or other aggregates when full child models are unnecessary; add these after a custom `select`. Use `chaperone()` for repeated child-to-parent traversal when supported. Detect lazy loading in development and tests. Automatic eager loading is an opt-in capability, globally or per collection; measure it before adopting it broadly. It does not bound relation cardinality or eliminate unnecessary hydration. [Eloquent relationships](https://laravel.com/docs/13.x/eloquent-relationships)

Bound large workloads. Prefer `chunkById`/`lazyById` when updating rows during iteration; group OR conditions because traversal adds predicates. Avoid changing traversal keys. `cursor()` cannot eager load and PDO buffering can still consume substantial memory. Bulk updates/deletes skip model events, so establish whether observers are part of the business behavior before replacing model saves. Preserve tenant scopes and soft-delete semantics. Eloquent does not support composite model primary keys; use a normal model key plus composite unique constraints where appropriate. [Eloquent](https://laravel.com/docs/13.x/eloquent)

## Measure and protect database invariants

Use query counts, timings, rows returned/examined, and the database's execution plan. `DB::listen` and cumulative `whenQueryingForLongerThan` monitoring can locate excessive work. Avoid logging sensitive bindings. Transactions roll back on exceptions and can retry deadlocks; keep external effects outside retryable callbacks. Read/write `sticky` behavior only provides writer reads within the current request after a write. Pooled PostgreSQL direct connections are a current documented capability; check the installed implementation for maintenance/migration routing. [Laravel database](https://laravel.com/docs/13.x/database)

Bind values and allowlist user-controlled identifiers. For read-modify-write invariants, use database constraints plus appropriate transaction isolation, atomic updates, or `lockForUpdate`. Keep locking transactions short and acquire competing resources consistently. Upsert relies on actual unique/primary indexes; MySQL and MariaDB use those indexes for collision detection rather than treating `uniqueBy` as a substitute for schema. Current vector queries support PostgreSQL with pgvector and MariaDB 11.7+; verify the driver, extension, dimensions, distance metric, indexing, and embedding-generation behavior before implementing semantic search. [Query builder](https://laravel.com/docs/13.x/queries)

## Pagination and schema

Use `paginate` when totals/page numbers are required; `simplePaginate` avoids the total-count query. Use cursor pagination for large changing feeds when a stable unique ordering is available. Add a unique tiebreaker and matching index; nullable order values and some expression forms are unsupported. Cursor pagination does not provide arbitrary numbered pages. [Pagination](https://laravel.com/docs/13.x/pagination)

Derive indexes from actual predicates, joins, ordering, selectivity, and uniqueness requirements; assess write overhead too. Inspect generated DDL for large-table changes. Current migration docs include engine-specific `online()`, `instant()`, and `lock()` controls, each with limitations. Check the database version and transaction restrictions. When altering columns with `change()`, restate modifiers that must survive and handle indexes explicitly. Plan compatible application/schema rollout and rollback for consequential changes. [Migrations](https://laravel.com/docs/13.x/migrations)

## Model behavior and representation

Use casts for domain values, dates, enums, encrypted values, and value objects. Null attributes are not cast; do not collide with primary keys or relationship names. Profile accessors and serialization when hydration is expensive. Encrypted casts require adequate storage and do not support ordinary indexed plaintext lookup. Test custom cast round trips and dirty tracking. Current vector casts require version verification. [Mutators and casts](https://laravel.com/docs/13.x/eloquent-mutators)

Keep authorization and output shape explicit when serializing models. Prefer API resources for response contracts and conditionally include already-loaded relationships instead of triggering new queries in serialization. Treat this as a review criterion and consult the matching version's resources/serialization docs for the implementation.

Separate class boot hooks from per-instance initialization. Conventional `boot{Trait}`/`initialize{Trait}` hooks coexist with current `#[Boot]`/`#[Initialize]` attributes. Preserve parent boot behavior and do not capture changing tenant/request state in class boot registrations. Inspect installed `Model.php` before relying on a newer attribute or hook ordering. [Framework Model source](https://raw.githubusercontent.com/laravel/framework/13.x/src/Illuminate/Database/Eloquent/Model.php)

## Upgrade and regression checks

Laravel 12→13 changes include rejection of empty MySQL/MariaDB upsert `uniqueBy`, honoring ORDER BY/LIMIT on joined MySQL deletes, pluralization of inferred custom polymorphic pivot tables, and rejection of recursive same-model instantiation during boot. Audit only applicable patterns and test against the real database engine. [Laravel 13 upgrade guide](https://laravel.com/docs/13.x/upgrade)

For a query change, compare results as well as timing. For state changes, exercise duplicate/concurrent writes, observer behavior, rollback, missing/deleted related models, and tenant isolation as relevant. SQLite-only tests cannot establish MySQL/PostgreSQL locking, index, or SQL semantics.
