# Redis and PhpRedis

## Choose and inspect the client

Laravel defaults to PhpRedis; Predis is a Composer-installed alternative. Identify `database.redis.client` and the extension available to each runtime: CLI, web server, queue worker, and Octane may use different PHP builds. Import `Illuminate\Support\Facades\Redis` explicitly; the extension's global `Redis` class is a different API.

Review connection/read timeouts, bounded reconnect backoff, connection names, persistence settings, TLS, and prefixes. Pipelining reduces round trips but is not an atomic transaction. Redis transactions and Lua scripts have distinct semantics. Cluster operations involving multiple keys require compatible hash slots. Current Laravel documents safe-read retries and configurable command retries; verify the installed connector before using them, and do not blindly replay non-idempotent writes after an ambiguous network failure. [Laravel Redis](https://laravel.com/docs/13.x/redis)

PhpRedis is a native extension with its own connection, serialization, compression, and command behavior. Inspect the installed extension version and enabled serializers before introducing igbinary, msgpack, LZF, LZ4, or Zstd. Test interoperability with existing values and every producer/consumer. A serialization change can require an explicit migration or a new key namespace. Check persistent-connection state and IDs when sharing processes across tenants or databases. Do not assume framework wrappers and raw extension calls return identical types. [PhpRedis API](https://phpredis.github.io/phpredis/Redis.html), [PhpRedis source](https://github.com/phpredis/phpredis)

## Match state to its failure model

Separate disposable cache from queues, locks, sessions, and authoritative state when their eviction/durability requirements differ. Redis eviction is an instance-level concern; logical database numbers do not isolate memory pressure. Consider separate instances for cache and persistent keys, size headroom, and monitor evictions and rejected writes. A no-eviction policy can reject writes when full, so it also requires capacity management. [Redis key eviction](https://redis.io/docs/latest/develop/reference/eviction/)

Redis Pub/Sub is at-most-once: disconnected consumers miss messages. Use it for live distribution with a durable source of truth and a resynchronization path where needed. Do not implement reliable business jobs solely with Pub/Sub. Redis Streams provide different persistence/consumer semantics and are not Laravel's standard Redis queue implementation. [Redis Pub/Sub](https://redis.io/docs/latest/develop/pubsub/)

## Cache and locks

Choose TTL and invalidation from the tolerated staleness. Namespace keys by application/environment and tenant where appropriate. Cache computed values rather than depending on stale model objects. `Cache::flexible` offers fresh/stale windows and refresh after the response; use it only when serving stale data is acceptable. A rebuild that must survive process failure belongs in durable work.

Use supported shared stores for atomic locks, with expiry exceeding the protected work's expected duration and explicit handling of acquisition failure. Ownership matters when releasing a lock from another process. Cache tags and store capabilities differ. `Cache::flush` ignores the configured prefix, so never use it as a scoped invalidation operation on shared storage. [Laravel cache](https://laravel.com/docs/13.x/cache)

## Verification

Test cache miss/hit/expiry, lock contention and expiry, client restart, timeout, and an ambiguous-write retry where relevant. For client migrations, verify representative strings, hashes, lists, scripts, queue payloads, and old cached values. Measure network round trips and server load before claiming a client or pipeline improves performance. Use sampled diagnostics; broad blocking key scans and verbose command tracing are poor defaults on busy systems.
