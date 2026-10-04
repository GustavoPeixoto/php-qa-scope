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
vendor/bin/php-qa-scope init
vendor/bin/php-qa-scope sync
vendor/bin/php-qa-scope check
```

If you prefer Composer script forwarding, add this to your project:

```json
{
    "scripts": {
        "qa-scope": "php-qa-scope"
    }
}
```

Then run:

```sh
composer qa-scope init
composer qa-scope sync
composer qa-scope check
```

## Initialize

For the initial setup, run this from your project root:

```sh
vendor/bin/php-qa-scope init
```

The command creates an absent scope YAML, prepares empty marker pairs in managed native configurations, then invokes `sync` to fill the blocks automatically. You do not need a separate `sync` invocation to populate them.

When native files change, the command prints this review message on standard error:

```plaintext
WARNING: QA configuration files were modified.
Review the changes and complete any required manual setup before running your QA tools.
Setup instructions: https://github.com/GustavoPeixoto/php-qa-scope#managed-blocks
```

Review the changes and complete the [manual setup](#managed-blocks) before running QA tools. A successful `init` means the package completed initialization and synchronization; it does not prove that the native tool configurations are ready to execute.

Target-local errors do not stop other managed files from being initialized. Successful changes remain in place if another target fails, and the command exits with code `2`. Correct the reported problem, place markers manually when needed, and rerun `init`. A target with an existing valid pair is still synchronized using its YAML scope; matching targets are not rewritten. An unchanged retry returns code `0` without the modification warning. Creating only the YAML also does not trigger that warning.

## Scope File

Run `vendor/bin/php-qa-scope init` to create `php-qa-scope.yml` when it is absent. The command detects only these exact filenames in your project root:

| Native file | YAML tool key |
| --- | --- |
| `phpcs.xml` | `phpcs` |
| `phpstan.neon` | `phpstan` |
| `php-cs-fixer.dist.php` | `php-cs-fixer` |

The generated YAML includes only `src` globally, leaves all excludes and tool-specific arrays empty, and lists only the detected tools. It does not copy scope settings from your native configurations or require `src` to exist yet. Review the default and adapt it to your project before running QA tools.

If no supported root file exists, `init` fails without creating YAML. Alternate filenames and configurations in subdirectories are not detected. Existing YAML is validated and preserved byte for byte; only its listed tools are managed, even if other native files are discovered.

You can also create `php-qa-scope.yml` manually, for example:

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

`init` inserts an empty managed block when both markers are absent, then invokes `sync` to fill it in the same command execution. Existing valid pairs are reused; incomplete, duplicated, reversed, or malformed pairs must be corrected manually.

Automatic placement supports conventional layouts. If a location cannot be recognized, the command reports a file-specific error and leaves that file unchanged. Place the markers manually as shown below and rerun `init`. Use exactly one pair per managed file and keep the required indentation.

PHPCS uses XML comments with four spaces of indentation, directly inside the first `ruleset`:

```xml
<ruleset name="App">
    <!-- php-qa-scope:start -->
    <!-- php-qa-scope:end -->
    <rule ref="PSR12"/>
</ruleset>
```

PHPStan uses `#` comments with four spaces of indentation, inside a top-level block-form `parameters:` section:

```neon
parameters:
    # php-qa-scope:start
    # php-qa-scope:end
    level: 6
```

PHP-CS-Fixer uses unindented `//` comments near the start of the PHP code, after required initial declarations:

```php
<?php

declare(strict_types=1);

// php-qa-scope:start
// php-qa-scope:end

return (new PhpCsFixer\Config())
    ->setRules(['@PSR12' => true])
    ->setFinder($finder);
```

Edit rules, levels, messages, and other tool-specific options outside managed blocks. `php-qa-scope` replaces only the managed block content.

PHPCS configurations with unsupported XML structures, PHPStan sections with inline or incompatible indentation layouts, and PHP-CS-Fixer configurations with namespaces or mixed PHP/non-PHP content need manual marker placement. A missing PHPStan `parameters` section is not created automatically. For PHPStan, align parameter entries with the markers' four spaces of indentation. In PHP, keep all required leading `declare` statements before the managed block so the generated Finder assignment does not precede `declare(strict_types=1)`.

### Review The Initial Setup

`init` preserves existing native content outside its inserted blocks. It does not migrate old scope settings or connect PHP-CS-Fixer's Finder to the returned configuration. Review these points after the command:

- PHPCS: reconcile existing global `<file>`, scope-related arguments, and `<exclude-pattern>` entries with the generated scope. Move the intended shared includes and exclusions into YAML. Keep rules and meaningful rule-specific settings outside the managed block.
- PHPStan: remove or reconcile old `paths` and `excludePaths` entries outside the managed block to avoid duplicate keys or conflicting selections. Express the intended scope in YAML and keep settings such as `level` outside the block.
- PHP-CS-Fixer: the filled block creates `$finder`. Connect it to your configuration with `->setFinder($finder)`, as in the example above. Reconcile existing Finder definitions, including assignments later in the file that would overwrite the generated variable, while preserving your rules, cache settings, and other options.

After adapting the YAML or correcting native settings, run `sync` and review the resulting diff. Then use `check` to verify that the managed blocks match the YAML. Neither command executes the QA tools or validates their complete native configurations.

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

Missing, duplicated, reversed, or malformed markers produce `ERROR <target>: <reason>` for that target. `check` and `sync` do not create markers automatically; use `init` or prepare markers manually. A target error does not stop either command from visiting later targets. `sync` may update valid targets and still finish with an error because another target failed. After fixing that error, rerun `sync`: it inspects every managed target and does not rewrite targets that are already synchronized.

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
| `0` | All checked targets are synchronized, or every managed target was already synchronized or successfully updated by `sync` or `init`. |
| `1` | `check` found at least one out-of-sync target and no errors. |
| `2` | Invalid arguments or project scope configuration, or at least one target error. Target errors take precedence over drift after all managed targets are visited. |

## Contributing

To contribute to this repository, read [AGENTS.md](AGENTS.md) and the documents in [conventions](conventions/) for development workflow, environment, and repository rules.
