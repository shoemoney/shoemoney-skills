# Octane and runtime performance

## Profile the service that is slow

Record request p50/p95/p99, throughput, errors, query time, and memory per worker using a representative dataset and concurrency. Separate application boot cost from database latency, external calls, serialization, and queue wait. Compare cold and warm behavior. Increasing worker count can exhaust database connections or increase contention; size it against CPU, memory, and downstream capacity.

Pulse exposes slow requests, jobs, queries, outgoing requests, and cache activity. Use existing telemetry first, selecting sample rates and excluding sensitive values. A quiet chart is insufficient evidence unless its ingestion path is working. [Laravel Pulse](https://laravel.com/docs/13.x/pulse)

## Worker lifetime

Octane supports FrankenPHP, RoadRunner, Swoole, and Open Swoole; the application boots once per worker. Service-provider boot logic is not per-request logic. Avoid retaining a request, container, configuration repository, authenticated user, or tenant in a long-lived object's constructor. Resolve current data at execution time. Watch static collections and retained references for memory growth. Exercise alternating users/tenants through the same worker, plus repeated requests and exceptions.

Swoole-family concurrent tasks, ticks, tables, and Octane cache are runtime-specific features. Octane tables/cache are local to a server and lost on restart; they are unsuitable as distributed durable state. Worker recycling limits the impact of leaks but does not fix them. Use the runtime's graceful reload mechanism after code changes. [Laravel Octane](https://laravel.com/docs/13.x/octane)

Use container `scoped` bindings for objects whose lifetime must be one request or job. A singleton is appropriate only when its state is safe for the entire worker lifetime. Current container documentation also describes `#[Scoped]`; verify the installed version before adopting attributes. [Service container](https://laravel.com/docs/13.x/container#binding-scoped-singletons)

## Concurrency is a separate choice

Laravel's Concurrency facade offers process, fork, and sync drivers. The fork driver requires `spatie/fork` and is CLI-only. Cross-process work should receive serializable data and create its own connections; avoid capturing a live request or connection. Parallel execution can increase pressure on a saturated dependency. Concurrency tasks and deferred work do not automatically supply durable queue retries. [Laravel concurrency](https://laravel.com/docs/13.x/concurrency)

## Deploy and verify

Build configuration/routes/events/views caches as appropriate for the actual deployment. After configuration caching, application code should use `config()` rather than calling `env()` outside configuration files. Current Laravel documents `php artisan reload` for long-running services; verify command availability and a process monitor that restarts terminated services. Older applications may require `queue:restart`, `horizon:terminate`, `octane:reload`, or `reverb:restart` as applicable.

`optimize:clear` also clears the default application cache. Choose targeted cache commands when the application cache must survive. Verify the active release, worker readiness, a real request/job, and graceful draining rather than treating a zero exit code as the whole deployment result. [Laravel deployment](https://laravel.com/docs/13.x/deployment)
