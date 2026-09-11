# Data types and schema design

## Model the domain before shrinking storage

Record allowed values, expected growth, NULL/default semantics, comparison rules, client representations, and precision requirements. A smaller column is beneficial only if the full valid domain still fits. Validate existing data and future inputs before narrowing, including foreign-key peers, ORM casts, APIs, import jobs, and replicas.

Integer widths consume 1/2/3/4/8 bytes for TINYINT/SMALLINT/MEDIUMINT/INT/BIGINT. UUID consumes 16 bytes; VARCHAR stores actual bytes plus a length prefix. Character counts are not byte counts. Treat temporal storage estimates as format-dependent. [Type storage requirements](https://mariadb.com/docs/server/reference/data-types/data-type-storage-requirements)

Choose signedness from the domain. BOOLEAN is an alias for TINYINT(1), not a constraint that accepts only zero and one. Use appropriate CHECK/application validation for a stricter domain. Strict SQL mode rejects many out-of-range values; non-strict operation can coerce with warnings. Display width is not the integer's storage size/range. `ZEROFILL` affects formatting and implies UNSIGNED. [Numeric overview](https://mariadb.com/docs/server/reference/data-types/numeric-data-types/numeric-data-type-overview), [INT](https://mariadb.com/docs/server/reference/data-types/numeric-data-types/int)

## Exact values and time

Use explicit `DECIMAL(M,D)` for exact decimal values such as prices and quantities requiring decimal arithmetic; M includes all digits and D is fractional scale. Do not substitute FLOAT/DOUBLE for money merely to reduce storage. Strict mode alone does not prohibit all fractional rounding, so test excess scale, overflow, aggregates, and client string/number conversion. Define rounding at the domain boundary. [DECIMAL](https://mariadb.com/docs/server/reference/data-types/numeric-data-types/decimal)

TIMESTAMP transforms session-local input to UTC and back on retrieval without storing a timezone identifier. Its upper range changes from 2038 to 2106 in MariaDB 11.5. First-TIMESTAMP implicit initialization/update depends on `explicit_defaults_for_timestamp`; write defaults and update behavior explicitly. Fractional precision ranges from zero to six digits. [TIMESTAMP](https://mariadb.com/docs/server/reference/data-types/date-and-time-data-types/timestamp)

DATETIME stores a calendar value without session-timezone conversion, supports years 1000–9999, and supports fractional precision. It can represent a UTC instant by application convention but does not enforce that convention. Preserve timezone identity separately for civil-time scheduling when needed, and test DST boundaries and SQL-mode handling of invalid/zero dates. [DATETIME](https://mariadb.com/docs/server/reference/data-types/date-and-time-data-types/datetime)

## Strings, collation, and row layout

Define VARCHAR lengths from the domain and use TEXT/BLOB for appropriate large payloads. Do not assume VARCHAR is always inline or TEXT always off-page. Trailing spaces can be stored yet compare equal depending on collation. Avoid accidentally changing equality while changing storage. [VARCHAR](https://mariadb.com/docs/server/reference/data-types/string-data-types/varchar)

Use explicit `utf8mb4` and intentional case/accent/padding behavior. Server/database/table/column/connection settings can differ; specifying a charset alone selects its default collation. Defaults changed in 11.6, and charset conversion can widen a TEXT-family type. Check resulting DDL and collision counts before conversion. [Setting character sets and collations](https://mariadb.com/docs/server/reference/data-types/string-data-types/character-sets/setting-character-sets-and-collations)

`utf8` is ambiguous across modes/versions. UCA versions, case/accent sensitivity, and PAD/NO PAD affect ordering and uniqueness. MySQL-compatible collation names in MariaDB can map to different Unicode rules; test comparison behavior rather than assuming name equality implies identical sorting. [Supported collations](https://mariadb.com/docs/server/reference/data-types/string-data-types/character-sets/supported-character-sets-and-collations)

Inspect actual row format and page size. Logical row-size limits and main-page storage limits are different. Overflow storage does not remove every row/index constraint. DYNAMIC/COMPRESSED index limits depend on page size; modern configurations should not inherit a universal 767-byte rule or a blanket VARCHAR(191) convention. [InnoDB row formats](https://mariadb.com/docs/server/server-usage/storage-engines/innodb/innodb-row-formats/innodb-row-formats-overview)

## JSON, generated values, and UUIDs

MariaDB JSON is a LONGTEXT alias with utf8mb4_bin semantics, not MySQL's binary JSON storage. Current alias behavior includes JSON validation; inspect historical schemas and server version. Keep stable constrained fields relational. For frequent JSON predicates, consider typed generated columns/indexes instead of parsing every row. Duplicate object keys and cross-product replication need explicit treatment. [JSON type](https://mariadb.com/docs/server/reference/data-types/string-data-types/json)

Both VIRTUAL and PERSISTENT generated columns can be indexed. Use deterministic expressions with explicit casts and session-stable behavior; review SQL-mode-dependent padding and unsigned subtraction. Direct optimizer recognition of indexed virtual-column expressions is available from 11.8, with exact-expression requirements; explicitly query the generated column when compatibility needs it. Generated-column foreign-key support has conflicting documentation: validate the exact engine/version/schema rather than claiming universal support. [Generated columns](https://mariadb.com/docs/server/reference/sql-statements/data-definition/create/generated-columns)

Native UUID is available from 10.7. Validate connector/ORM representation and insertion locality; handling of newer UUID variants changes across maintenance releases. Native UUID support does not imply support for every UUID-generation function, and MySQL byte-swapping recipes are not portable defaults. [UUID type](https://mariadb.com/docs/server/reference/data-types/string-data-types/uuid-data-type)

Before a type change, compare old/new round trips, boundary values, NULLs, precision, timezone, collation collisions, and index feasibility. See [locks and DDL](locks-ddl.md) for deployment costs.
