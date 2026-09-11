# Documentation, complementary skills, and Boost

## Load relevant skills deliberately

Read the active skill catalog and applicable repository instructions. Load the actual matching `SKILL.md` and the references needed for the task; merely naming a skill does not use it. Maria's core library is self-contained and does not require an unrelated plugin.

For Laravel/Eloquent work, use **Taytay** when available: model casts, decimal/JSON/UUID serialization, migrations, N+1 queries, relationship loading, transactions, queue workers, Redis caches, and persistent connections can change database behavior. Maria owns MariaDB execution/storage semantics; use Taytay's application knowledge to trace the complete path. A Laravel connection called `mysql` can point to MariaDB and is not a server-version check.

Other skills can provide codebase conventions, test procedures, observability, SQL review, or fleet/Galera operations. Use them when their scope matches the assignment. Treat historical tuning recipes as hypotheses: check MariaDB-specific syntax, release gates, and measured effects against primary sources. Do not inherit blanket index-count limits, universal memory ratios, or MySQL-only optimizer commands from a generic SQL skill.

Use an authorized subagent only for a concrete independent research/review/implementation task that benefits from parallel work. Give it the relevant files, target version, bounded responsibility, and verification criteria. Do not assume a newly installed role is callable in an already-running session's catalog.

## Retrieve current official evidence

Start with the topic references in this folder. Use official MariaDB Server, Galera, release-note, and relevant connector documentation; inspect version tabs and maintenance-release notes. Confirm consequential defaults and syntax against the real server/installed code. Documentation for the newest release is not automatically applicable to an older server.

The [official documentation index](https://mariadb.com/docs/llms.txt) lists current pages. Search it for a missing topic, then retrieve the specific page; do not load the entire documentation corpus into the prompt. MariaDB supports Markdown by appending `.md`. If a browser fetch cannot handle `text/markdown`, use an available HTTP/text fetcher for the same official page. Check the title/body as well as the HTTP status: moved URLs can return a successful status with a “Page Not Found” body.

Record source URL, access date, target version/edition, and uncertainty for consequential findings. When docs disagree, use release notes, installed metadata/source, or a controlled reproduction to resolve the conflict. State remaining ambiguity instead of manufacturing certainty. For features outside this library—such as vector indexes, ColumnStore, MaxScale, Spider, proxy routing, or a particular connector—retrieve the relevant official documentation on demand.

## Use available database tools

Discover actual connectors/MCP tools before invoking them. Confirm which host, database, identity, and environment the tool targets. Begin with necessary metadata and narrow diagnostics within the user's authorized scope. A schema or SQL tool may still permit writes; its name is not proof of read-only behavior. Do not expose credentials or unnecessary row contents in outputs.

Use [diagnostics.sql](diagnostics.sql) as a menu, not an unattended script. Check permissions, metadata availability, and collection overhead. Explain when statistics are approximate or instrumentation is missing. Separate static advice, estimated plans, executed measurements, and production observations in the result.

## Publish Maria or another relevant skill through Boost

Boost's MCP tools and agent skills are complementary. A skill is an instruction folder exposed to the coding agent; adding it does not add a SQL tool to the MCP server. In a Laravel project, custom skills belong in `.ai/skills/<name>/SKILL.md`, with relative references and YAML `name`/`description` frontmatter. Package-owned skills use `resources/boost/skills/<name>/SKILL.md`. [Official Boost documentation](https://laravel.com/docs/13.x/boost)

1. Inspect the installed Boost version, current `boost.json`, existing skill sources, and selected coding agents. Preserve existing skills and configuration.
2. Author or copy the complete portable skill folder under `.ai/skills`. Check naming collisions deliberately; custom names can override bundled skills.
3. Check the installed command help. For an initialized Boost 2.7 project, `php artisan boost:update --no-discover --no-interaction` refreshes selected agents without prompting for newly detected packages. Use supported options for other versions. Initialize with `boost:install` only when setup is actually missing.
4. Confirm `php artisan boost:list-skills` discovers the source, then inspect the generated agent folder/link and read its `SKILL.md` and references. Discovery alone does not prove publication. Boost 2.7 normally publishes to `.agents/skills` for Codex and `.claude/skills` for Claude Code; configuration may override those paths.
5. Verify the next session's catalog or invocation before claiming runtime activation. A running session may need a new task/reload to see a new role or skill.

These publishing details were checked against Boost 2.7 source. [UpdateCommand](https://github.com/laravel/boost/blob/v2.7.0/src/Console/UpdateCommand.php), [SkillWriter](https://github.com/laravel/boost/blob/v2.7.0/src/Install/SkillWriter.php), [Codex adapter](https://github.com/laravel/boost/blob/v2.7.0/src/Install/Agents/Codex.php)

For external skills, inspect repository contents and choose only the relevant skill using the installed `boost:add-skill` interface. Do not bulk-install unknown guidance or overwrite local customizations as a substitute for research. [AddSkillCommand](https://github.com/laravel/boost/blob/v2.7.0/src/Console/AddSkillCommand.php)

When Boost MCP is available, discover its real tools and use application/package info and focused documentation searches. Its Laravel package-aware search is useful for the application side; it is not a substitute for MariaDB server documentation. Database/schema tools and Tinker require scope-aware use; Tinker executes application code. If MCP is unavailable, use installed source and official docs and describe that limitation accurately. [Boost tools](https://github.com/laravel/boost/blob/v2.7.0/src/Mcp/Boost.php)
