# Events, notifications, broadcasting, and Reverb

## Events and listeners

Use events for domain facts and listeners for reactions. `ShouldQueue` makes a listener asynchronous; `ShouldQueueAfterCommit` postpones listener enqueueing. `ShouldDispatchAfterCommit` postpones the event itself until commit. `Event::defer` buffers events during a closure and discards them on an exception; it is not a transaction boundary. Current queued listeners support middleware, encryption, failure handling, and uniqueness features; verify version-specific contracts. Cache event discovery for deployment when appropriate.

Test listeners independently from event-dispatch assertions. `Event::fake` suppresses listeners, including model events needed by factories; create fixtures before faking when necessary. [Laravel events](https://laravel.com/docs/13.x/events)

## Notifications

Queued delivery fans out per recipient/channel. Budget that expansion, route channels using `viaConnections`/`viaQueues`, and set delays/middleware for provider behavior. Use `afterCommit()` for committed-state dependencies and `shouldSend` to recheck current preferences/state at processing time. Preserve locale and minimize payloads. `toDatabase` can differ from the `toArray` representation used for broadcasts. Broadcast notifications are queued; `BroadcastMessage` controls their queue/connection and recipients subscribe to private channels. Version-check newer hooks such as `afterSending`.

Distinguish enqueueing, provider acceptance, and confirmed delivery. Verify recipient, channel, payload, locale, and routing with focused assertions, then test the real transport when delivery behavior changes. [Laravel notifications](https://laravel.com/docs/13.x/notifications)

## Broadcast contract and security

`ShouldBroadcast` queues a broadcast; choose synchronous `ShouldBroadcastNow` only when its latency/failure semantics fit. Define `broadcastOn` and an explicit `broadcastWith` payload; public properties are otherwise exposed by default. Private and presence channels require authorization, including explicit tenant/resource ownership checks. Channel model binding is not automatic scoped authorization. Presence member data is visible to other members.

Custom `broadcastAs` names need Echo's leading-dot convention. `toOthers` depends on the originating socket ID reaching the server. Release listeners/channels when components disappear. Client whispers are untrusted ephemeral UI signals, not server-authorized state changes. [Laravel broadcasting](https://laravel.com/docs/13.x/broadcasting)

## Reverb transport and scale

Separate listen settings (`REVERB_SERVER_HOST/PORT`) from Laravel's broadcast destination (`REVERB_HOST/PORT`) and browser-facing Echo settings. Configure appropriate origins and TLS; origins do not replace channel authorization. Reverse proxies must route `/app` and `/apps`, preserve WebSocket upgrades, and handle long-lived connections. Reverb needs a process manager and graceful restart.

Size process/OS file limits, proxy limits, and event-loop capacity together. The default select-based loop has limitations; Reverb can use `ext-uv` when installed. Avoid assuming a single universal connection maximum. Horizontal scaling uses shared Redis Pub/Sub and a load balancer. Pulse integration can record connections/messages; in a scaled setup, run the documented `pulse:check` polling on one server. [Laravel Reverb](https://laravel.com/docs/13.x/reverb)

## Trace and verify end-to-end

Give a test operation an identifier and follow committed record → event → queued listener/broadcast → worker → Reverb → authorized subscription → browser update. Test an authorized subscriber and a denied user from another tenant, payload redaction, reconnect/resubscription, listener cleanup, and ordering/duplicate handling as relevant.

Use HTTP or another durable state read to reconcile after reconnect when missed events matter. Sequence/version identifiers can prevent stale updates from overwriting newer UI state. Treat these as application design choices, not automatic Reverb guarantees. Diagnose the first missing stage instead of restarting every service. Never infer delivery merely from a working handshake or an empty job queue.
