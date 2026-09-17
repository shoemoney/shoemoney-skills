# Optional Stop hook

Verified contract: [official Codex hook documentation](https://developers.openai.com/codex/hooks). Stop consumes JSON stdin and emits JSON stdout. `decision: block` requests continuation; `stop_hook_active` prevents recursion. Exact hook definitions require user trust through `/hooks`; never edit the trust store or bypass it to claim activation.

`scripts/change_guard.py` only acts inside projects with `.executive-brief.json`. It hashes watched nonignored Git files, skips dotfiles/private/secrets/vendor paths, and compares an acknowledged baseline. It sends nothing, runs no model, executes no project-supplied commands, and doesn't publish or alter production. The agent determines whether nominated changes are material.

Project example:

```json
{
  "watch": ["app/*", "config/*", "database/*", "resources/*", "routes/*", "runtime/*", "ops/*", "composer.json", "composer.lock", "package.json", "package-lock.json"],
  "briefing": "outputs/briefings/index.json"
}
```

Git-ignore `.executive-brief/` (state/cloud-change markers). Track the config and a project instruction: “After a material hardware/software change, use $executive-brief to append a verified v+1 edition preserving all earlier content and evidence. Mark external infrastructure changes; acknowledge after publication or documented deferral.” This remains useful without trusted hook support.

Merge into `~/.codex/hooks.json`, preserving existing hooks. Substitute and shell-quote the installed absolute script path:

```json
{
  "hooks": {
    "Stop": [{"hooks": [{
      "type": "command",
      "command": "python3 '<installed-skill>/scripts/change_guard.py' hook",
      "timeout": 10
    }]}]
  }
}
```

Review/trust in `/hooks`, then test a new session's real lifecycle. Direct script tests prove behavior, not runtime loading. Check Claude Code's current contract before adapting this to its settings.

```sh
python3 <skill>/scripts/change_guard.py acknowledge --root <project> --note 'vN published and live-verified'
python3 <skill>/scripts/change_guard.py mark --root <project> --note 'Resized cloud worker; verify live state'
```

Errors surface a warning, not a session trap. Each changed fingerprint requests at most one continuation until another change; acknowledged state stays quiet. New opted-in projects request a baseline review. Incomplete evidence means a dated in-progress edition or precise deferral, never invented completion.

File hashes cannot see cloud-console changes: call `mark`. Hooks act when a turn finishes in the configured project; they don't wake idle sessions or schedule monitoring. This is a workflow aid, not a security boundary.
