## 1. Context and Baseline

- [x] 1.1 Read `proposal.md`, `design.md`, `AGENTS.md`, and the applicable language, repository, workflow, Git, artifacts, environment, context-mode, and PHPDoc conventions before editing; verify that the working tree and current Unit files still match the relocation-only scope and the destination table.
- [x] 1.2 In the package PHP environment, capture `vendor/bin/phpunit --testsuite Unit --list-tests` and the current Unit class/method inventory, then run `composer test`; verify that all 19 existing Unit classes are discovered and record any pre-existing failures before relocation. Keep baseline evidence transient and record any material blocker in the change itself.

## 2. Relocate Existing Unit Tests

- [x] 2.1 Move the 16 files other than `CliTest.php`, `ConsoleTest.php`, and the unchanged `ToolTest.php` to their destinations in `design.md`, updating each moved namespace; verify every destination and PSR-4 namespace against the table, with existing class names, methods, imports, assertions, and fixture content preserved except any qualified test reference required by the namespace move.
- [x] 2.2 Move `CliTest.php` to `Cli/` and `ConsoleTest.php` to `Console/`, update their namespaces, and replace their two executable lookups with `dirname(__DIR__, 3) . '/bin/php-qa-scope'`; verify the existing scenarios pass with `vendor/bin/phpunit --testsuite Unit --filter '(CliTest|ConsoleTest)'` and that fixture/rendering strings containing `__DIR__` remain unchanged.
- [x] 2.3 Compare `vendor/bin/phpunit --testsuite Unit --list-tests` with the baseline, normalizing only the intended test namespace changes, and run `vendor/bin/phpunit --testsuite Unit`; verify identical discovered class/method coverage, all 19 classes retained, no duplicate old files, and only `ToolTest.php` remaining directly under `tests/Unit/`.

## 3. Integration and Change Review

- [x] 3.1 Run `composer test`, `composer sniffer-check`, `composer stan-check`, and `composer fixer-check -- --allow-risky=yes` in the package PHP environment; verify the complete existing suites and native QA checks pass, identifying any failure already present in the baseline rather than broadening the change to unrelated fixes.
- [x] 3.2 Review the rename-aware diff and compare it with `design.md`; verify that implementation edits consist only of the 18 relocations, their namespace or necessary qualified test-reference adjustments, and the two executable-path fixes, while production code, shared helpers, Integration tests, Composer metadata, QA configuration, fixtures, assertions, and test methods remain unchanged.
- [x] 3.3 Audit the planning artifacts for parity with the final mapping and independence from transient baseline evidence, then run `openspec validate organize-unit-tests --strict` and `git diff --check`; verify that both checks pass, `skip_specs: true` remains declared, no delta specs exist, and no relevant open question remains.
