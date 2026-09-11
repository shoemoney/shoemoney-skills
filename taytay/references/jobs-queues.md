# Jobs, queues, and Horizon

## Choose the delivery contract

Use a durable queue when work must survive process failure and retry. Make side effects idempotent using a durable operation key/unique constraint and provider idempotency support where available. Record success and reconcile ambiguous provider results; an in-memory flag or cache lock cannot establish exactly-once business effects.

`ShouldBeUnique` suppresses duplicate dispatch, `ShouldBeUniqueUntilProcessing` releases the dispatch lock before execution, and `WithoutOverlapping` limits simultaneous execution. These mechanisms need correctly shared cache state; uniqueness does not apply inside batches. Lock expiry and release behavior must match the work. Middleware releases consume attempts. Keep worker timeout below `retry_after`, and bound external I/O separately. Set retry attempts, backoff, retry deadline, and failure behavior intentionally. Use `after_commit`/`afterCommit()` when jobs depend on committed records. [Laravel 12 queue reliability documentation](https://laravel.com/docs/12.x/queues)

## Payloads and composition

Serialized Eloquent jobs restore records and loaded relations without retaining the original relation constraints. Use IDs or `withoutRelations`/`#[WithoutRelations]`, then requery the needed state at execution time. Handle missing records explicitly.

Use chains for dependent steps, batches for tracked parallel work and cancellation, and `Bus::bulk` for independent dispatch without batch tracking when supported. Cancellation requires cooperation. Deleting a chain job does not stop the chain; use the supported failure/control mechanism. Batch callbacks should not capture `$this` or perform statements that implicitly commit transactions.

Current 13.x docs describe `#[DebounceFor]`, `debounceId`, `debounceVia`, `maxWait`, `PreparesForDispatch`, and queue routing/attributes. Verify the exact class and dispatch path before using them. Debounce and `ShouldBeUnique` are mutually exclusive. Deferred/background/failover connections also appear in current 12.x docs; do not label them all 13-only. [Laravel 13 queues](https://laravel.com/docs/13.x/queues)

## Important failure windows

Failover writes attempt configured connections in order, but `pop` and queue metrics delegate to the first connection. Provision consumers and alerts for **every concrete durable fallback queue**. A synchronous fallback changes request latency and failure behavior. An ambiguous first enqueue followed by fallback can duplicate work; account for that in the business operation. [FailoverQueue source](https://raw.githubusercontent.com/laravel/framework/13.x/src/Illuminate/Queue/FailoverQueue.php)

The background connection extends the synchronous queue and schedules a separate process through Concurrency. It is not broker-backed durable storage and is not managed as a Redis queue by Horizon. Use it only when that failure model is acceptable. [BackgroundQueue source](https://raw.githubusercontent.com/laravel/framework/13.x/src/Illuminate/Queue/BackgroundQueue.php)

Debounce skips jobs whose owner was superseded, but allows execution when its cache key is missing. It is coalescing, not durable exclusion. Business effects precede job acknowledgment, so a crash can cause replay. Make chain steps and callbacks safe under the actual failure/retry model. [CallQueuedHandler source](https://raw.githubusercontent.com/laravel/framework/13.x/src/Illuminate/Queue/CallQueuedHandler.php)

`PendingDispatch` runs `prepareForDispatch` before acquiring uniqueness; `false` cancels dispatch. Lower-level insertion paths may not run its hooks. Verify the entrypoint used by the application rather than assuming every enqueue behaves identically. [PendingDispatch source](https://raw.githubusercontent.com/laravel/framework/13.x/src/Illuminate/Foundation/Bus/PendingDispatch.php)

Check dependencies before failover too: uniqueness acquisition happens before enqueueing. If its lock store is the failed Redis service, dispatch can fail before reaching the database fallback. Inspect `uniqueVia()` and debounce/cache dependencies as part of outage design. Use a shared store that meets the required availability model, or avoid making dispatch depend on that lock while retaining durable business idempotency. Test the whole producer path during the outage.

## Operate Horizon deliberately

Horizon requires Redis queues and does not support Redis Cluster. Its internal `horizon` connection name is reserved. Auto balancing allocates capacity by workload, not strict queue priority; use separate supervisors for explicit resource allocation. Set attempts deliberately, accounting for middleware releases. With auto balancing, keep job timeout below Horizon timeout and Horizon timeout below `retry_after`.

Monitor oldest wait, failed jobs, throughput, runtime, and worker memory alongside database/API capacity. Schedule `horizon:snapshot` every five minutes for metrics. Protect the dashboard outside local development. Deploy with graceful termination and a process monitor, then verify replacement workers use the new release. [Laravel Horizon](https://laravel.com/docs/13.x/horizon)

## Test the behavior that can fail

Fakes establish dispatch/chain/batch intent. Exercise the handler's real state changes separately. Where reliability is changed, test the concrete queue backend, duplicate execution, timeout/retry, rollback before dispatch, provider ambiguity, cancellation, and worker restart as applicable. An empty primary queue does not prove fallback queues are drained.
