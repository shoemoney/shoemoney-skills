#!/usr/bin/env python3
"""Read package/runtime facts without booting Laravel or reading environment files."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


def relevant(name):
    return name.startswith(("laravel/", "illuminate/", "livewire/", "inertiajs/", "filament/")) or name in {
        "predis/predis", "pusher/pusher-php-server", "phpunit/phpunit", "pestphp/pest",
        "spiral/roadrunner-cli", "spiral/roadrunner-http", "spatie/fork",
    }


def read_json(path, warnings):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as error:
        warnings.append(f"Cannot parse {path.name}: {type(error).__name__}")
        return None


def package_versions(packages):
    if not isinstance(packages, list):
        return {}
    return {
        item["name"]: item.get("version", "unknown")
        for item in packages
        if isinstance(item, dict) and isinstance(item.get("name"), str) and relevant(item["name"])
    }


def inspect(root, php):
    warnings = []
    manifest = read_json(root / "composer.json", warnings)
    if not isinstance(manifest, dict):
        raise ValueError("A readable composer.json object is required.")
    declared = {}
    for section in ("require", "require-dev"):
        dependencies = manifest.get(section, {})
        if isinstance(dependencies, dict):
            declared.update({k: v for k, v in dependencies.items() if k == "php" or k.startswith("ext-") or relevant(k)})
    lock = read_json(root / "composer.lock", warnings)
    locked = package_versions(lock.get("packages", [])) if isinstance(lock, dict) else {}
    if isinstance(lock, dict):
        locked.update(package_versions(lock.get("packages-dev", [])))
    installed_data = read_json(root / "vendor/composer/installed.json", warnings)
    installed = package_versions(installed_data.get("packages", []) if isinstance(installed_data, dict) else installed_data)
    if not lock:
        warnings.append("Locked versions unavailable; dependency constraints are not installed versions.")
    if installed_data is None:
        warnings.append("Installed package metadata unavailable; verify the deployed runtime separately.")
    mismatches = {
        name: {"locked": locked.get(name), "installed": installed.get(name)}
        for name in sorted(locked.keys() | installed.keys())
        if installed_data is not None and locked.get(name) != installed.get(name)
    }
    runtime = {"available": False}
    executable = shutil.which(php)
    if executable:
        code = '$names=["redis","swoole","openswoole","pcntl","pdo_mysql","pdo_pgsql","pdo_sqlite","uv","igbinary","msgpack","Zend OPcache"]; $out=["php"=>PHP_VERSION,"sapi"=>PHP_SAPI,"extensions"=>[]]; foreach($names as $name){$out["extensions"][$name]=extension_loaded($name)?(phpversion($name)?:true):false;} echo json_encode($out);'
        try:
            result = subprocess.run([executable, "-r", code], capture_output=True, text=True, timeout=10, check=True)
            runtime = {"available": True, "executable": executable, **json.loads(result.stdout)}
        except (OSError, subprocess.SubprocessError, ValueError):
            warnings.append("CLI PHP inspection failed; no application code was executed.")
    else:
        warnings.append("CLI PHP executable unavailable.")
    skill_roots = (".ai/skills", ".agents/skills", ".claude/skills", ".codex/skills")
    skills = {
        folder: sorted(p.parent.name for p in (root / folder).glob("*/SKILL.md"))
        for folder in skill_roots
    }
    return {
        "project": str(root), "artisan_present": (root / "artisan").is_file(),
        "declared": declared, "locked": locked, "installed": installed,
        "version_mismatches": mismatches, "cli_runtime": runtime,
        "boost_config_present": (root / "boost.json").is_file(), "skills": skills,
        "limitations": "CLI facts only; no Laravel bootstrap, .env, credentials, database connections, or live service probes.",
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--php", default="php", help="PHP executable path/name for CLI extension inspection")
    args = parser.parse_args()
    try:
        result = inspect(Path(args.project).expanduser().resolve(), args.php)
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
