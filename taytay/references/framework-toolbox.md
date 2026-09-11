# Laravel framework toolbox

Use the existing application architecture. A feature being available is not a reason to add it. Choose the smallest framework mechanism that expresses the behavior, and load its installed-version documentation through Boost before implementation.

## Traits and composition

Use a trait for cohesive reusable behavior that belongs on its host class, a service for dependencies/orchestration, a scope for reusable query constraints, and an observer for model lifecycle reactions. Avoid hidden I/O in traits or accessors. Make requirements explicit and test behavior through a concrete host. PHP precedence is class method → trait method → inherited method; resolve collisions intentionally with `insteadof` and aliases. An alias does not remove the original method. [PHP traits manual](https://www.php.net/manual/en/language.oop5.traits.php)

For Eloquent traits, use the boot/initialize guidance in [Eloquent and database](eloquent-database.md). Do not store per-request identity in static boot state.

## Scheduling and external work

Choose `withoutOverlapping` for concurrent-run exclusion and `onOneServer` for one scheduler across hosts; configure a shared supported lock store and distinct names for parameterized tasks. Lock lifetime and recovery need to match expected work. Account for daylight-saving transitions when using local timezones. Sub-minute schedules need the documented interruption behavior during deployment. Schedule durable jobs when the work belongs on a queue; the scheduler's existence does not prove consumers are running. [Task scheduling](https://laravel.com/docs/13.x/scheduling)

Set outbound HTTP connection and total timeouts. Retry selectively with backoff and respect request idempotency; avoid replaying payments or other non-idempotent writes without a provider-supported key. Laravel's HTTP client does not automatically throw for all HTTP error responses; inspect status or use explicit throwing behavior. Use fakes plus stray-request prevention in isolated tests and real transport checks when integration behavior changes. [HTTP client](https://laravel.com/docs/13.x/http-client)

## Response contracts, authorization, and tests

Use resources for stable output contracts, conditional loaded relationships, and pagination metadata. Keep large object graphs out of payloads. JSON:API is a distinct response format; adopt it when the client's contract calls for it, with matching documentation. [API resources](https://laravel.com/docs/13.x/eloquent-resources)

Use policies/gates around actual resources and actions, including tenant ownership. Validation and mass-assignment configuration are not authorization. Test denied as well as permitted operations. [Authorization](https://laravel.com/docs/13.x/authorization)

Use the project's Pest/PHPUnit setup and test environment. `RefreshDatabase` commonly uses transactions once the schema is ready; tests relying on actual commit timing or separate workers need an appropriate integration setup. Factories, database assertions, and query-count expectations can support focused regressions. Parallel tests need isolated shared resources, not just isolated database names. [Database testing](https://laravel.com/docs/13.x/database-testing), [Testing](https://laravel.com/docs/13.x/testing)

## Documentation routing for the rest of Laravel

This is an on-demand lookup map, not a claim that every linked subsystem was exhaustively researched. Resolve links to the application's major version and package versions before using them.

| Concern | Official documentation to load |
| --- | --- |
| Application boot and dependency boundaries | [Lifecycle](https://laravel.com/docs/13.x/lifecycle), [container](https://laravel.com/docs/13.x/container), [providers](https://laravel.com/docs/13.x/providers), [contracts](https://laravel.com/docs/13.x/contracts) |
| HTTP application | [Routing](https://laravel.com/docs/13.x/routing), [middleware](https://laravel.com/docs/13.x/middleware), [requests](https://laravel.com/docs/13.x/requests), [responses](https://laravel.com/docs/13.x/responses), [validation](https://laravel.com/docs/13.x/validation) |
| Authentication and security | [Authentication](https://laravel.com/docs/13.x/authentication), [Sanctum](https://laravel.com/docs/13.x/sanctum), [Passport](https://laravel.com/docs/13.x/passport), [CSRF](https://laravel.com/docs/13.x/csrf), [encryption](https://laravel.com/docs/13.x/encryption), [hashing](https://laravel.com/docs/13.x/hashing), [rate limiting](https://laravel.com/docs/13.x/rate-limiting) |
| Presentation and client integration | [Blade](https://laravel.com/docs/13.x/blade), [Vite](https://laravel.com/docs/13.x/vite), [frontend](https://laravel.com/docs/13.x/frontend), [localization](https://laravel.com/docs/13.x/localization), [Precognition](https://laravel.com/docs/13.x/precognition) |
| Data structures and output | [Collections](https://laravel.com/docs/13.x/collections), [Eloquent collections](https://laravel.com/docs/13.x/eloquent-collections), [serialization](https://laravel.com/docs/13.x/eloquent-serialization), [factories](https://laravel.com/docs/13.x/eloquent-factories) |
| Files, sessions, mail, and processes | [Filesystem](https://laravel.com/docs/13.x/filesystem), [session](https://laravel.com/docs/13.x/session), [mail](https://laravel.com/docs/13.x/mail), [processes](https://laravel.com/docs/13.x/processes), [Artisan](https://laravel.com/docs/13.x/artisan) |
| Diagnostics and context | [Errors](https://laravel.com/docs/13.x/errors), [logging](https://laravel.com/docs/13.x/logging), [context](https://laravel.com/docs/13.x/context), [Telescope](https://laravel.com/docs/13.x/telescope), [Pulse](https://laravel.com/docs/13.x/pulse) |
| Search, AI, tools, packages | [Scout](https://laravel.com/docs/13.x/scout), [AI SDK](https://laravel.com/docs/13.x/ai-sdk), [MCP](https://laravel.com/docs/13.x/mcp), [package development](https://laravel.com/docs/13.x/packages), [Pennant](https://laravel.com/docs/13.x/pennant) |
| Test layers and formatting | [HTTP tests](https://laravel.com/docs/13.x/http-tests), [console tests](https://laravel.com/docs/13.x/console-tests), [mocking](https://laravel.com/docs/13.x/mocking), [Dusk](https://laravel.com/docs/13.x/dusk), [Pint](https://laravel.com/docs/13.x/pint) |

For Livewire, Inertia, Filament, Nova, or other installed ecosystem packages, use Boost's detected package versions and relevant package skills; these packages have their own release cycles.
