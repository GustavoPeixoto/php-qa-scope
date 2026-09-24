# php-qa-scope

`php-qa-scope` keeps the file scope of PHP QA tools synchronized from one small YAML file.

It reads `php-qa-scope.yml`, computes the effective scope for each supported tool, and updates or checks only managed blocks in native configuration files.

It is not a QA runner. It does not define PHPStan levels, PHPCS standards, PHP-CS-Fixer rules, or tool-specific policy.

## Why php-qa-scope?

PHP projects often repeat the same file selection across several QA tools:

- PHPStan has its own `paths` and `excludePaths`.
- PHPCS has XML files and exclude patterns.
- PHP-CS-Fixer has a Finder configured in PHP.

Those declarations drift over time. One tool may scan `src/`, another may include `tests/`, and another may silently ignore a directory that was supposed to be checked.

`php-qa-scope` makes the shared question explicit:

```text
Which files should our QA tools inspect?
```

You keep each tool's native configuration and policy. `php-qa-scope` only synchronizes the managed file-scope block.

## Install

Install it as a development dependency:

```sh
composer require --dev gustavo-peixoto/php-qa-scope
```

The package exposes the `php-qa-scope` binary through Composer:

```sh
vendor/bin/php-qa-scope check
vendor/bin/php-qa-scope sync
```

If you prefer Composer script forwarding, add this to your project:

```json
{
    "scripts": {
        "php-qa-scope": "php-qa-scope"
    }
}
```

Then run:

```sh
composer php-qa-scope check
composer php-qa-scope sync
```

## Scope File

Create `php-qa-scope.yml` in your project root:

```yaml
include:
  - src
  - tests
  - bin

exclude: []

tools:
  phpstan:
    include: []
    exclude: []

  phpcs:
    include: []
    exclude: []

  php-cs-fixer:
    include: []
    exclude: []
```

Directories are recursive. Files ending in `.php` are treated as specific files. New files inside included directories automatically enter the tool selection; adding, removing, or renaming a PHP file does not require a new `sync`.

> [!WARNING]
> During recursive scans, PHPStan and PHP-CS-Fixer ignore files and directories whose names begin with `.`. PHPCS ignores dotfiles but can enter hidden directories, and its dotfile behavior cannot be configured. To keep their file selections aligned, `sync` may add PHPCS include-selection and hidden-directory exclusion patterns even when YAML `exclude` is empty. List a hidden PHP file or directory explicitly in `include` to select it; configured excludes still win.

The `tools` map declares which tools are managed. Keep a tool key when the project uses that tool. Remove a tool key when the project does not use that tool. For each listed tool, `include` and `exclude` must be present and may be empty arrays.

For example, a project that uses PHPStan and PHP-CS-Fixer but not PHPCS may omit `phpcs`:

```yaml
include:
  - src
  - tests

exclude: []

tools:
  phpstan:
    include: []
    exclude: []

  php-cs-fixer:
    include: []
    exclude: []
```

The effective scope for each tool is:

```text
(global include + tools.<tool>.include)
    - (global exclude + tools.<tool>.exclude)
```

Tool-specific includes add paths; they do not replace global includes. Excludes always win, with no re-inclusion.

Accepted tool keys are:

- `phpcs`
- `phpstan`
- `php-cs-fixer`

PHPMD is not managed yet because its usual workflow receives the file list from the command invocation rather than from a native configuration block equivalent to PHPStan, PHPCS, or PHP-CS-Fixer. `php-qa-scope` currently synchronizes persistent config blocks only; adding PHPMD support would require a clear strategy for generating or wrapping the analyzed path list without turning the package into a QA runner.

## Managed Blocks

Add one managed block to each supported tool configuration.

PHPCS uses XML comments:

```xml
<!-- php-qa-scope:start -->
<!-- php-qa-scope:end -->
```

PHPStan uses `#` comments:

```neon
# php-qa-scope:start
# php-qa-scope:end
```

PHP-CS-Fixer uses `//` comments:

```php
// php-qa-scope:start
// php-qa-scope:end
```

Edit rules, levels, messages, and other tool-specific options outside managed blocks. `php-qa-scope` replaces only the managed block content.

## Sync And Check

After changing the scope file, synchronize the native tool configurations:

```sh
vendor/bin/php-qa-scope sync
```

Use `check` in CI to verify committed configuration files are already synchronized:

```sh
vendor/bin/php-qa-scope check
```

Both commands inspect each managed target independently. `check` reports `OK` or `OUT-OF-SYNC` for valid targets without changing files. `sync` reports `OK` for a matching target or replaces only the managed block of a divergent target and reports `UPDATED`. The rest of each updated file is preserved byte for byte.

Missing, duplicated, reversed, or malformed markers produce `ERROR <target>: <reason>` for that target; the command does not create markers automatically. A target error does not stop either command from visiting later targets. `sync` may update valid targets and still finish with an error because another target failed. After fixing that error, rerun `sync`: it inspects every managed target and does not rewrite targets that are already synchronized.

Target statuses appear on standard output, while `ERROR` lines appear on standard error. There is no built-in unified diff; review changes with Git after `sync`.

## Supported Exclude Patterns

The package intentionally supports a small portable pattern language rather than arbitrary glob syntax.

| Form | Example | Match |
| --- | --- | --- |
| Specific file | `src/Compatibility.php` | Only that file |
| Specific subtree | `tests/fixtures/**` | All descendants of the directory |
| Recurring directory | `**/legacy/**` | Descendants of `legacy` at any depth |
| Recurring directory under a root | `config/**/legacy/**` | Descendants of `legacy` inside `config` |
| File suffix | `**/*Generated.php` | Files ending in `Generated.php` at any depth |

The YAML does not support `plugins/*/vendor/**`, `src/*.php`, `**/Generated*.php`, `?`, `[]` classes, `{}` alternatives, `!` negation, or regular expressions.

## Exit Codes

| Code | Meaning |
| --- | --- |
| `0` | All checked targets are synchronized, or every sync target was already synchronized or successfully updated. |
| `1` | `check` found at least one out-of-sync target and no errors. |
| `2` | Invalid arguments or project scope configuration, or at least one target error. Target errors take precedence over drift after all managed targets are visited. |

## Contributing

To contribute to this repository, read [AGENTS.md](AGENTS.md) and the documents in [conventions](conventions/) for development workflow, environment, and repository rules.
