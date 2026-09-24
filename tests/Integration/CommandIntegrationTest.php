<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Integration;

use GustavoPeixoto\PhpQaScope\Application;
use GustavoPeixoto\PhpQaScope\Cli\ExitCode;
use GustavoPeixoto\PhpQaScope\Sync\SyncWriter;
use GustavoPeixoto\PhpQaScope\Sync\TargetInspector;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use RuntimeException;
use Symfony\Component\Yaml\Yaml;

/**
 * Covers end-to-end command behavior against temporary project fixtures.
 */
final class CommandIntegrationTest extends TestCase
{
    /**
     * Verifies check and sync status output and exit codes.
     */
    public function testCheckAndSyncStatusesAndExitCodes(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, []);
        $app = Application::default();

        [$code, $stdout] = $this->runApp($app, ['php-qa-scope', 'check'], $root);
        self::assertSame(ExitCode::DRIFT, $code);
        self::assertStringContainsString("OUT-OF-SYNC phpcs.xml\n", $stdout);
        self::assertStringContainsString("OUT-OF-SYNC phpstan.neon\n", $stdout);
        self::assertStringContainsString("OUT-OF-SYNC php-cs-fixer.dist.php\n", $stdout);

        $before = file_get_contents($root . '/phpcs.xml');
        self::assertIsString($before);
        self::assertStringContainsString('    <!-- outside -->', $before);

        [$code, $stdout] = $this->runApp($app, ['php-qa-scope', 'sync'], $root);
        self::assertSame(ExitCode::SUCCESS, $code);
        self::assertStringContainsString("UPDATED phpcs.xml\n", $stdout);
        self::assertStringContainsString('    <!-- outside -->', (string) file_get_contents($root . '/phpcs.xml'));

        [$code, $stdout] = $this->runApp($app, ['php-qa-scope', 'check'], $root);
        self::assertSame(ExitCode::SUCCESS, $code);
        self::assertStringContainsString("OK phpcs.xml\n", $stdout);
    }

    /**
     * Verifies sync preserves CRLF line endings and remains idempotent.
     */
    public function testSyncPreservesCrLfOutsideManagedBlockAndIsIdempotent(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, []);
        $xml = (string) file_get_contents($root . '/phpcs.xml');
        $this->put($root, 'phpcs.xml', str_replace("\n", "\r\n", $xml));

        $app = Application::default();
        self::assertSame(ExitCode::SUCCESS, $this->runApp($app, ['php-qa-scope', 'sync'], $root)[0]);

        $synced = (string) file_get_contents($root . '/phpcs.xml');
        self::assertStringContainsString("    <!-- outside -->\r\n", $synced);
        self::assertSame(0, preg_match('/(?<!\r)\n/', $synced));
        self::assertSame(ExitCode::SUCCESS, $this->runApp($app, ['php-qa-scope', 'sync'], $root)[0]);
    }

    /**
     * Verifies validation errors are converted to the package error exit code.
     */
    public function testValidationErrorReturnsExitCodeTwo(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, []);
        $this->put($root, 'phpcs.xml', 'broken');

        [$code, , $stderr] = $this->runApp(Application::default(), ['php-qa-scope', 'check'], $root);

        self::assertSame(ExitCode::ERROR, $code);
        self::assertStringContainsString('ERROR phpcs.xml: expected exactly one php-qa-scope:start marker.', $stderr);
    }

    /**
     * Verifies sync refuses to overwrite files changed after inspection.
     */
    public function testConcurrentChangePreventsOverwrite(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, []);
        $planner = TargetInspector::default();
        $writer = new SyncWriter();
        $inspection = $planner->inspect($root, 'phpcs', $planner->scopes($root)['phpcs']);
        $this->put($root, 'phpcs.xml', 'concurrent edit');

        try {
            $writer->write($root, $inspection);
            self::fail('Concurrent edit should fail.');
        } catch (RuntimeException) {
            self::assertSame('concurrent edit', file_get_contents($root . '/phpcs.xml'));
            self::assertSame([], glob($root . '/.php-qa-scope-*'));
        }
    }

    /**
     * Verifies a failed target write removes its temporary file.
     */
    public function testWritePreparationFailureCleansTemporaryFile(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, []);
        $planner = TargetInspector::default();
        $inspection = $planner->inspect($root, 'phpcs', $planner->scopes($root)['phpcs']);
        unlink($root . '/phpcs.xml');

        try {
            (new SyncWriter())->write($root, $inspection);
            self::fail('Preparing a missing target should fail.');
        } catch (RuntimeException) {
            self::assertFileDoesNotExist($root . '/phpcs.xml');
            self::assertSame([], glob($root . '/.php-qa-scope-*'));
        }
    }

    /**
     * Verifies sync continues after an invalid first target and reports mixed results.
     */
    public function testSyncReportsMixedResultsAndRetriesWithoutRewriting(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, []);
        $planner = TargetInspector::default();
        $fixer = $planner->inspect($root, 'php-cs-fixer', $planner->scopes($root)['php-cs-fixer']);
        $this->put($root, 'php-cs-fixer.dist.php', $fixer->replacement());
        $this->put($root, 'phpstan.neon', 'broken');
        $app = Application::default();

        [$code, $stdout, $stderr] = $this->runApp($app, ['php-qa-scope', 'sync'], $root);

        self::assertSame(ExitCode::ERROR, $code);
        self::assertSame("UPDATED phpcs.xml\nOK php-cs-fixer.dist.php\n", $stdout);
        self::assertStringContainsString(
            'ERROR phpstan.neon: expected exactly one php-qa-scope:start marker.',
            $stderr,
        );
        self::assertSame('broken', file_get_contents($root . '/phpstan.neon'));
        $updated = (string) file_get_contents($root . '/phpcs.xml');
        $inode = fileinode($root . '/phpcs.xml');

        $this->put($root, 'phpstan.neon', "parameters:\n    # php-qa-scope:start\n    # php-qa-scope:end\n");
        [$code, $stdout, $stderr] = $this->runApp($app, ['php-qa-scope', 'sync'], $root);

        self::assertSame(ExitCode::SUCCESS, $code);
        self::assertSame("UPDATED phpstan.neon\nOK phpcs.xml\nOK php-cs-fixer.dist.php\n", $stdout);
        self::assertSame('', $stderr);
        self::assertSame($updated, file_get_contents($root . '/phpcs.xml'));
        clearstatcache(true, $root . '/phpcs.xml');
        self::assertSame($inode, fileinode($root . '/phpcs.xml'));
    }

    /**
     * Verifies a later invalid target does not undo an earlier update.
     */
    public function testSyncKeepsEarlierUpdateWhenLaterTargetFails(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, []);
        $this->put($root, 'phpcs.xml', 'broken');

        [$code, $stdout, $stderr] = $this->runApp(Application::default(), ['php-qa-scope', 'sync'], $root);

        self::assertSame(ExitCode::ERROR, $code);
        self::assertStringContainsString("UPDATED phpstan.neon\n", $stdout);
        self::assertStringContainsString("UPDATED php-cs-fixer.dist.php\n", $stdout);
        self::assertStringContainsString('ERROR phpcs.xml:', $stderr);
        self::assertStringContainsString('paths:', (string) file_get_contents($root . '/phpstan.neon'));
        self::assertSame('broken', file_get_contents($root . '/phpcs.xml'));
    }

    /**
     * Verifies check visits later targets and gives errors precedence over drift.
     */
    public function testCheckContinuesAfterLocalError(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, []);
        $this->put($root, 'phpstan.neon', 'broken');

        [$code, $stdout, $stderr] = $this->runApp(Application::default(), ['php-qa-scope', 'check'], $root);

        self::assertSame(ExitCode::ERROR, $code);
        self::assertStringContainsString("OUT-OF-SYNC phpcs.xml\n", $stdout);
        self::assertStringContainsString("OUT-OF-SYNC php-cs-fixer.dist.php\n", $stdout);
        self::assertStringContainsString('ERROR phpstan.neon:', $stderr);
    }

    /**
     * Verifies invalid project scope stops both commands before native access.
     */
    public function testInvalidScopeFailsBeforeNativeTargets(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, []);
        $this->put($root, 'phpstan.neon', 'native sentinel');

        $invalidConfigurations = [
            'tools: [invalid',
            Yaml::dump([
                'include' => [],
                'exclude' => [],
                'tools' => ['phpstan' => ['include' => [], 'exclude' => []]],
            ], 5),
        ];

        foreach ($invalidConfigurations as $configuration) {
            $this->put($root, 'php-qa-scope.yml', $configuration);
            foreach (['check', 'sync'] as $command) {
                [$code, $stdout, $stderr] = $this->runApp(Application::default(), ['php-qa-scope', $command], $root);
                self::assertSame(ExitCode::ERROR, $code);
                self::assertSame('', $stdout);
                self::assertStringContainsString('ERROR ', $stderr);
                self::assertStringNotContainsString('ERROR phpstan.neon:', $stderr);
                self::assertSame('native sentinel', file_get_contents($root . '/phpstan.neon'));
            }
        }
    }

    /**
     * Verifies a target update preserves mode and rejects symbolic links.
     */
    public function testSyncPreservesModeAndRejectsSymbolicLink(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, []);
        chmod($root . '/phpcs.xml', 0640);
        $app = Application::default();
        self::assertSame(ExitCode::SUCCESS, $this->runApp($app, ['php-qa-scope', 'sync'], $root)[0]);
        self::assertSame(0640, fileperms($root . '/phpcs.xml') & 0777);

        unlink($root . '/phpcs.xml');
        symlink($root . '/phpstan.neon', $root . '/phpcs.xml');
        [$code, $stdout, $stderr] = $this->runApp($app, ['php-qa-scope', 'sync'], $root);
        self::assertSame(ExitCode::ERROR, $code);
        self::assertStringContainsString('ERROR phpcs.xml:', $stderr);
        self::assertStringContainsString("OK phpstan.neon\n", $stdout);
        self::assertTrue(is_link($root . '/phpcs.xml'));
        self::assertSame([], glob($root . '/.php-qa-scope-*'));
    }

    /**
     * Runs the application with in-memory output streams.
     *
     * @param Application $app Application instance to execute.
     * @param list<string> $argv Command-line arguments including the executable name.
     * @param string $root Project root for the run.
     * @return array{0: int, 1: string, 2: string} Exit code, stdout, and stderr.
     */
    private function runApp(Application $app, array $argv, string $root): array
    {
        $stdout = fopen('php://memory', 'w+');
        $stderr = fopen('php://memory', 'w+');
        $code = $app->run($argv, $root, $stdout, $stderr);
        rewind($stdout);
        rewind($stderr);

        return [$code, stream_get_contents($stdout), stream_get_contents($stderr)];
    }
}
