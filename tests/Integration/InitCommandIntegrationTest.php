<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Integration;

use GustavoPeixoto\PhpQaScope\Application;
use GustavoPeixoto\PhpQaScope\Cli\ExitCode;
use GustavoPeixoto\PhpQaScope\Command\CommandRegistry;
use GustavoPeixoto\PhpQaScope\Command\InitCommand;
use GustavoPeixoto\PhpQaScope\Scope\ScopeLoader;
use GustavoPeixoto\PhpQaScope\Scope\ToolScope;
use GustavoPeixoto\PhpQaScope\Initializer\Initializer;
use GustavoPeixoto\PhpQaScope\Target\TargetInitializer;
use GustavoPeixoto\PhpQaScope\InsertionLocator\InsertionLocator;
use GustavoPeixoto\PhpQaScope\InsertionLocator\InsertionLocatorRegistry;
use GustavoPeixoto\PhpQaScope\Renderer\Renderer;
use GustavoPeixoto\PhpQaScope\Renderer\RendererRegistry;
use GustavoPeixoto\PhpQaScope\Block\ManagedBlock;
use GustavoPeixoto\PhpQaScope\Target\TargetWriter;
use GustavoPeixoto\PhpQaScope\Synchronizer\Synchronizer;
use GustavoPeixoto\PhpQaScope\Target\TargetInspector;
use GustavoPeixoto\PhpQaScope\Target\TargetRegistry;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use RuntimeException;

/**
 * Exercises consumer initialization, automatic synchronization, and retry behavior.
 */
final class InitCommandIntegrationTest extends TestCase
{
    /**
     * Creates defaults and fills every native block in one initialization execution.
     */
    public function testInitializesAndSynchronizesAllTools(): void
    {
        $root = $this->tempRoot();
        $original = $this->rawProject($root);
        $result = $this->runApp(Application::default(), $root);

        self::assertSame(ExitCode::SUCCESS, $result['code']);
        self::assertSame("UPDATED phpcs.xml\nUPDATED phpstan.neon\nUPDATED php-cs-fixer.dist.php\n", $result['stdout']);
        self::assertSame(InitCommand::REVIEW_WARNING . "\n", $result['stderr']);
        $config = (new ScopeLoader())->load($root . '/php-qa-scope.yml');
        self::assertSame(['src'], $config->include);
        self::assertSame(['phpcs', 'phpstan', 'php-cs-fixer'], $config->managedTools());

        $registry = new TargetRegistry();
        foreach ($config->managedTools() as $tool) {
            $target = $registry->get($tool);
            $contents = (string) file_get_contents($root . '/' . $target->path);
            $block = (new ManagedBlock())->locate($contents, $target);
            self::assertSame(
                RendererRegistry::default()->get($tool)->render(new ToolScope(['src'], [])),
                $block->content,
            );
            self::assertSame(1, substr_count($contents, 'php-qa-scope:start'));
            self::assertSame(1, substr_count($contents, 'php-qa-scope:end'));
        }
        self::assertStringContainsString('<rule ref="PSR12"/>', (string) file_get_contents($root . '/phpcs.xml'));
        self::assertStringContainsString('    level: 6', (string) file_get_contents($root . '/phpstan.neon'));
        self::assertStringEndsWith(
            substr($original['php-cs-fixer.dist.php'], strlen("<?php\n")),
            (string) file_get_contents($root . '/php-cs-fixer.dist.php'),
        );
        self::assertSame(ExitCode::SUCCESS, $this->runApp(Application::default(), $root, 'check')['code']);
    }

    /**
     * Observes all persisted empty pairs when synchronization first renders a target.
     */
    public function testPersistsAllEmptyPairsBeforeRendering(): void
    {
        $root = $this->tempRoot();
        $this->rawProject($root);
        $observer = new class ($root) implements Renderer {
            public int $calls = 0;

            /**
             * Captures the project whose prepared files will be observed.
             *
             * @param string $root Project root being initialized.
             */
            public function __construct(private readonly string $root)
            {
            }

            /**
             * Checks all empty pairs before delegating to the standard PHPCS renderer.
             *
             * @param ToolScope $scope Scope passed to synchronization.
             * @return string Standard PHPCS managed fragment.
             */
            public function render(ToolScope $scope): string
            {
                ++$this->calls;
                $targets = new TargetRegistry();
                foreach (['phpcs', 'phpstan', 'php-cs-fixer'] as $tool) {
                    $target = $targets->get($tool);
                    $contents = (string) file_get_contents($this->root . '/' . $target->path);
                    InitCommandIntegrationTest::assertSame(
                        '',
                        (new ManagedBlock())->locate($contents, $target)->content,
                    );
                }

                return RendererRegistry::default()->get('phpcs')->render($scope);
            }
        };
        $defaults = RendererRegistry::default();
        $inspector = new TargetInspector(renderers: new RendererRegistry([
            'phpcs' => $observer,
            'phpstan' => $defaults->get('phpstan'),
            'php-cs-fixer' => $defaults->get('php-cs-fixer'),
        ]));
        $app = new Application(new CommandRegistry([
            new InitCommand(
                new Initializer(
                    new Synchronizer($inspector, new TargetWriter()),
                    new TargetInitializer(InsertionLocatorRegistry::default()),
                ),
            ),
        ]));

        self::assertSame(ExitCode::SUCCESS, $this->runApp($app, $root)['code']);
        self::assertSame(1, $observer->calls);
        self::assertSame(ExitCode::SUCCESS, $this->runApp(Application::default(), $root, 'check')['code']);
    }

    /**
     * Synchronizes only existing YAML's selected tools and preserves its custom scope.
     */
    public function testExistingYamlControlsSelectionAndExistingBlockSynchronization(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, [
            'include' => ['app'],
            'tools' => ['phpstan' => ['include' => ['tests'], 'exclude' => []]],
        ]);
        $yaml = file_get_contents($root . '/php-qa-scope.yml');
        $phpcs = file_get_contents($root . '/phpcs.xml');
        $fixer = file_get_contents($root . '/php-cs-fixer.dist.php');
        $result = $this->runApp(Application::default(), $root);

        self::assertSame(ExitCode::SUCCESS, $result['code']);
        self::assertSame("UPDATED phpstan.neon\n", $result['stdout']);
        self::assertSame(InitCommand::REVIEW_WARNING . "\n", $result['stderr']);
        self::assertSame($yaml, file_get_contents($root . '/php-qa-scope.yml'));
        self::assertSame($phpcs, file_get_contents($root . '/phpcs.xml'));
        self::assertSame($fixer, file_get_contents($root . '/php-cs-fixer.dist.php'));
        self::assertStringContainsString("        - 'app'", (string) file_get_contents($root . '/phpstan.neon'));
        self::assertStringContainsString("        - 'tests'", (string) file_get_contents($root . '/phpstan.neon'));
    }

    /**
     * Continues after a preparation error and retries without rewriting successful targets.
     */
    public function testPreparationFailureContinuesAndRetryPreservesSuccessfulTargets(): void
    {
        $root = $this->tempRoot();
        $original = $this->rawProject($root);
        $this->put($root, 'phpcs.xml', '<ruleset/>');
        $app = Application::default();
        $result = $this->runApp($app, $root);

        self::assertSame(ExitCode::ERROR, $result['code']);
        self::assertSame("UPDATED phpstan.neon\nUPDATED php-cs-fixer.dist.php\n", $result['stdout']);
        self::assertSame(1, substr_count($result['stderr'], 'ERROR phpcs.xml:'));
        self::assertStringContainsString('Place the markers manually', $result['stderr']);
        self::assertStringEndsWith(InitCommand::REVIEW_WARNING . "\n", $result['stderr']);
        self::assertSame('<ruleset/>', file_get_contents($root . '/phpcs.xml'));
        $inode = fileinode($root . '/phpstan.neon');

        $this->put($root, 'phpcs.xml', $original['phpcs.xml']);
        $retry = $this->runApp($app, $root);
        self::assertSame(ExitCode::SUCCESS, $retry['code']);
        self::assertSame("UPDATED phpcs.xml\nOK phpstan.neon\nOK php-cs-fixer.dist.php\n", $retry['stdout']);
        clearstatcache(true, $root . '/phpstan.neon');
        self::assertSame($inode, fileinode($root . '/phpstan.neon'));
        self::assertSame(ExitCode::SUCCESS, $this->runApp($app, $root, 'check')['code']);
    }

    /**
     * Reports missing listed files and native links locally while synchronizing a valid target.
     */
    public function testMissingTargetsAndNativeLinksRemainLocalErrors(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, []);
        unlink($root . '/phpcs.xml');
        unlink($root . '/php-cs-fixer.dist.php');
        $this->put($root, 'actual.php', 'consumer configuration');
        symlink($root . '/actual.php', $root . '/php-cs-fixer.dist.php');
        $result = $this->runApp(Application::default(), $root);

        self::assertSame(ExitCode::ERROR, $result['code']);
        self::assertSame("UPDATED phpstan.neon\n", $result['stdout']);
        self::assertStringContainsString('ERROR phpcs.xml: could not read', $result['stderr']);
        self::assertStringContainsString(
            'ERROR php-cs-fixer.dist.php: managed configuration files cannot be symbolic links',
            $result['stderr'],
        );
        self::assertTrue(is_link($root . '/php-cs-fixer.dist.php'));
        self::assertSame('consumer configuration', file_get_contents($root . '/actual.php'));
        self::assertFileDoesNotExist($root . '/phpcs.xml');
        self::assertSame([], glob($root . '/.php-qa-scope-*'));
    }

    /**
     * Retains an inserted empty pair after a rendering error and processes later targets.
     */
    public function testSyncFailureRetainsPreparationAndStillProcessesLaterTargets(): void
    {
        $root = $this->tempRoot();
        $this->rawProject($root);
        $failure = new class () implements Renderer {
            /**
             * Simulates a target-local rendering error after all pairs are persisted.
             *
             * @param ToolScope $scope Effective scope for the failing target.
             * @return string Rendered fragment when rendering succeeds.
             */
            public function render(ToolScope $scope): string
            {
                throw new RuntimeException('simulated rendering failure');
            }
        };
        $defaults = RendererRegistry::default();
        $inspector = new TargetInspector(renderers: new RendererRegistry([
            'phpcs' => $failure,
            'phpstan' => $defaults->get('phpstan'),
            'php-cs-fixer' => $defaults->get('php-cs-fixer'),
        ]));
        $app = new Application(new CommandRegistry([
            new InitCommand(
                new Initializer(
                    new Synchronizer($inspector, new TargetWriter()),
                    new TargetInitializer(InsertionLocatorRegistry::default()),
                ),
            ),
        ]));
        $result = $this->runApp($app, $root);

        self::assertSame(ExitCode::ERROR, $result['code']);
        self::assertSame("UPDATED phpstan.neon\nUPDATED php-cs-fixer.dist.php\n", $result['stdout']);
        self::assertStringContainsString('ERROR phpcs.xml: simulated rendering failure', $result['stderr']);
        self::assertStringEndsWith(InitCommand::REVIEW_WARNING . "\n", $result['stderr']);
        self::assertSame('', (new ManagedBlock())->locate(
            (string) file_get_contents($root . '/phpcs.xml'),
            (new TargetRegistry())->get('phpcs'),
        )->content);
        $inode = fileinode($root . '/phpstan.neon');

        self::assertSame(ExitCode::SUCCESS, $this->runApp(Application::default(), $root)['code']);
        clearstatcache(true, $root . '/phpstan.neon');
        self::assertSame($inode, fileinode($root . '/phpstan.neon'));
        self::assertSame(ExitCode::SUCCESS, $this->runApp(Application::default(), $root, 'check')['code']);
    }

    /**
     * Stops command-wide YAML failures before modifying any native configuration.
     */
    public function testInvalidYamlStopsBeforeAnyNativeWrite(): void
    {
        $root = $this->tempRoot();
        $original = $this->rawProject($root);
        $yaml = "include: []\nexclude: []\ntools: {}\n";
        $this->put($root, 'php-qa-scope.yml', $yaml);
        $result = $this->runApp(Application::default(), $root);

        self::assertSame(ExitCode::ERROR, $result['code']);
        self::assertSame('', $result['stdout']);
        self::assertStringNotContainsString('WARNING', $result['stderr']);
        self::assertSame($yaml, file_get_contents($root . '/php-qa-scope.yml'));
        foreach ($original as $file => $contents) {
            self::assertSame($contents, file_get_contents($root . '/' . $file));
        }
    }

    /**
     * Refuses a concurrent file mutation between marker inspection and replacement.
     */
    public function testConcurrentPreparationChangeIsPreserved(): void
    {
        $root = $this->tempRoot();
        $this->put($root, 'phpstan.neon', "parameters:\n    level: 6\n");
        $locator = new class ($root) implements InsertionLocator {
            /**
             * Captures the target to mutate during placement.
             *
             * @param string $root Root of the concurrent-change fixture.
             */
            public function __construct(private readonly string $root)
            {
            }

            /**
             * Simulates a concurrent native edit after the preparer has read its bytes.
             *
             * @param string $contents Original inspected configuration bytes.
             * @return int Original insertion boundary.
             */
            public function locate(string $contents): int
            {
                file_put_contents($this->root . '/phpstan.neon', 'concurrent configuration');

                return (int) strpos($contents, "\n") + 1;
            }
        };
        $app = new Application(new CommandRegistry([
            new InitCommand(
                new Initializer(
                    new Synchronizer(TargetInspector::default(), new TargetWriter()),
                    markers: new TargetInitializer(locators: new InsertionLocatorRegistry(['phpstan' => $locator])),
                ),
            ),
        ]));
        $result = $this->runApp($app, $root);

        self::assertSame(ExitCode::ERROR, $result['code']);
        self::assertStringContainsString('changed during init', $result['stderr']);
        self::assertStringNotContainsString('WARNING', $result['stderr']);
        self::assertSame('concurrent configuration', file_get_contents($root . '/phpstan.neon'));
        self::assertSame([], glob($root . '/.php-qa-scope-*'));
    }

    /**
     * Emits the exact consumer message once, then leaves an unchanged retry silent.
     */
    public function testWarningTextAndNoOpRetry(): void
    {
        $root = $this->tempRoot();
        $this->rawProject($root);
        $app = Application::default();
        $first = $this->runApp($app, $root);
        $warning = "WARNING: QA configuration files were modified.\n"
            . "Review the changes and complete any required manual setup before running your QA tools.\n"
            . "Setup instructions: https://github.com/GustavoPeixoto/php-qa-scope#managed-blocks\n";
        self::assertSame($warning, $first['stderr']);
        self::assertStringNotContainsString('WARNING', $first['stdout']);
        $files = ['php-qa-scope.yml', 'phpcs.xml', 'phpstan.neon', 'php-cs-fixer.dist.php'];
        $inodes = [];
        foreach ($files as $file) {
            $inodes[$file] = fileinode($root . '/' . $file);
        }

        $retry = $this->runApp($app, $root);
        self::assertSame(ExitCode::SUCCESS, $retry['code']);
        self::assertSame("OK phpcs.xml\nOK phpstan.neon\nOK php-cs-fixer.dist.php\n", $retry['stdout']);
        self::assertSame('', $retry['stderr']);
        foreach ($files as $file) {
            clearstatcache(true, $root . '/' . $file);
            self::assertSame($inodes[$file], fileinode($root . '/' . $file));
        }
    }

    /**
     * Does not claim native modifications when only a new YAML is created.
     */
    public function testYamlOnlyCreationDoesNotWarnOrRewriteNativeFiles(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, ['include' => ['src']]);
        $app = Application::default();
        self::assertSame(ExitCode::SUCCESS, $this->runApp($app, $root, 'sync')['code']);
        $inodes = [];
        foreach (['phpcs.xml', 'phpstan.neon', 'php-cs-fixer.dist.php'] as $file) {
            $inodes[$file] = fileinode($root . '/' . $file);
        }
        unlink($root . '/php-qa-scope.yml');

        $result = $this->runApp($app, $root);
        self::assertSame(ExitCode::SUCCESS, $result['code']);
        self::assertSame('', $result['stderr']);
        self::assertFileExists($root . '/php-qa-scope.yml');
        foreach ($inodes as $file => $inode) {
            clearstatcache(true, $root . '/' . $file);
            self::assertSame($inode, fileinode($root . '/' . $file));
        }
    }

    /**
     * Warns after an inserted empty pair even if no synchronization write succeeds.
     */
    public function testPreparationOnlyChangesStillWarnAfterSyncFailure(): void
    {
        $root = $this->tempRoot();
        $this->put($root, 'phpstan.neon', "parameters:\n    level: 6\n");
        $failure = new class () implements Renderer {
            /**
             * Fails the only target's synchronization after successful preparation.
             *
             * @param ToolScope $scope Effective scope passed to the renderer.
             * @return string Fragment produced on a successful render.
             */
            public function render(ToolScope $scope): string
            {
                throw new RuntimeException('rendering failed');
            }
        };
        $inspector = new TargetInspector(renderers: new RendererRegistry(['phpstan' => $failure]));
        $app = new Application(new CommandRegistry([
            new InitCommand(
                new Initializer(
                    new Synchronizer($inspector, new TargetWriter()),
                    new TargetInitializer(InsertionLocatorRegistry::default()),
                ),
            ),
        ]));
        $result = $this->runApp($app, $root);

        self::assertSame(ExitCode::ERROR, $result['code']);
        self::assertSame('', $result['stdout']);
        self::assertSame(
            "ERROR phpstan.neon: rendering failed\n" . InitCommand::REVIEW_WARNING . "\n",
            $result['stderr'],
        );
        self::assertSame(1, substr_count($result['stderr'], 'WARNING:'));
    }

    /**
     * Omits the modification warning when every target fails before any native write.
     */
    public function testAllPreparationFailuresDoNotWarn(): void
    {
        $root = $this->tempRoot();
        $this->put($root, 'phpcs.xml', '<ruleset/>');
        $result = $this->runApp(Application::default(), $root);

        self::assertSame(ExitCode::ERROR, $result['code']);
        self::assertSame('', $result['stdout']);
        self::assertStringNotContainsString('WARNING:', $result['stderr']);
        self::assertSame('<ruleset/>', file_get_contents($root . '/phpcs.xml'));
    }

    /**
     * Preserves CRLF, permissions, and exact bytes outside inserted rendered blocks.
     */
    public function testCrLfAndOutsideBytesArePreservedAcrossBothPhases(): void
    {
        $root = $this->tempRoot();
        $original = $this->rawProject($root, "\r\n");
        foreach (array_keys($original) as $file) {
            chmod($root . '/' . $file, 0640);
        }
        self::assertSame(ExitCode::SUCCESS, $this->runApp(Application::default(), $root)['code']);
        $prefixes = [
            'phpcs' => "<?xml version=\"1.0\"?>\r\n<ruleset name=\"App\">",
            'phpstan' => "parameters:\r\n",
            'php-cs-fixer' => "<?php\r\n",
        ];
        $targets = new TargetRegistry();
        foreach ($prefixes as $tool => $prefix) {
            $target = $targets->get($tool);
            $rendered = RendererRegistry::default()->get($tool)->render(new ToolScope(['src'], []));
            $pair = ($tool === 'phpcs' ? "\r\n" : '')
                . $target->indent . sprintf($target->marker, 'start') . "\r\n"
                . str_replace("\n", "\r\n", $rendered)
                . $target->indent . sprintf($target->marker, 'end') . "\r\n";
            $expected = $prefix . $pair . substr($original[$target->path], strlen($prefix));
            self::assertSame($expected, file_get_contents($root . '/' . $target->path));
            self::assertSame(0640, fileperms($root . '/' . $target->path) & 0777);
        }
        self::assertSame(ExitCode::SUCCESS, $this->runApp(Application::default(), $root, 'check')['code']);
    }

    /**
     * Initializes every supported tool individually without creating other native targets.
     */
    public function testEachIsolatedToolCompletesAndChecksSuccessfully(): void
    {
        $targets = new TargetRegistry();
        foreach (['phpcs', 'phpstan', 'php-cs-fixer'] as $tool) {
            $root = $this->tempRoot();
            $original = $this->rawProject($root);
            $file = $targets->get($tool)->path;
            foreach (array_keys($original) as $other) {
                if ($other !== $file) {
                    unlink($root . '/' . $other);
                }
            }
            $result = $this->runApp(Application::default(), $root);
            self::assertSame(ExitCode::SUCCESS, $result['code']);
            self::assertSame("UPDATED $file\n", $result['stdout']);
            self::assertSame([$tool], (new ScopeLoader())->load($root . '/php-qa-scope.yml')->managedTools());
            self::assertSame(ExitCode::SUCCESS, $this->runApp(Application::default(), $root, 'check')['code']);
            foreach (array_keys($original) as $other) {
                if ($other !== $file) {
                    self::assertFileDoesNotExist($root . '/' . $other);
                }
            }
        }
    }

    /**
     * Fails discovery before touching either absent or existing YAML in an empty project.
     */
    public function testNoRecognizedRootFilesCauseNoWrites(): void
    {
        foreach ([false, true] as $existingYaml) {
            $root = $this->tempRoot();
            $yaml = "include: [src]\nexclude: []\ntools: {}\n";
            $this->put($root, 'config/phpstan.neon', "parameters:\n");
            if ($existingYaml) {
                $this->put($root, 'php-qa-scope.yml', $yaml);
            }
            $result = $this->runApp(Application::default(), $root);
            self::assertSame(ExitCode::ERROR, $result['code']);
            self::assertStringContainsString('No supported QA configuration', $result['stderr']);
            self::assertStringNotContainsString('WARNING', $result['stderr']);
            if ($existingYaml) {
                self::assertSame($yaml, file_get_contents($root . '/php-qa-scope.yml'));
            } else {
                self::assertFileDoesNotExist($root . '/php-qa-scope.yml');
            }
        }
    }

    /**
     * Keeps an incomplete pair unchanged and reports it once while updating other targets.
     */
    public function testInvalidMarkersRemainUnchangedAndAreNotRetriedDuringSync(): void
    {
        $root = $this->tempRoot();
        $this->rawProject($root);
        $bad = "parameters:\n    # php-qa-scope:start\n";
        $this->put($root, 'phpstan.neon', $bad);
        $result = $this->runApp(Application::default(), $root);

        self::assertSame(ExitCode::ERROR, $result['code']);
        self::assertSame("UPDATED phpcs.xml\nUPDATED php-cs-fixer.dist.php\n", $result['stdout']);
        self::assertSame(1, substr_count($result['stderr'], 'ERROR phpstan.neon:'));
        self::assertSame($bad, file_get_contents($root . '/phpstan.neon'));
    }

    /**
     * Creates conventional native fixtures without managed markers.
     *
     * @param string $root Project root receiving the fixtures.
     * @param string $eol Newline convention used by the native files.
     * @return array<string, string> Original bytes indexed by native filename.
     */
    private function rawProject(string $root, string $eol = "\n"): array
    {
        $files = [
            'phpcs.xml' => "<?xml version=\"1.0\"?>\n<ruleset name=\"App\">\n    <rule ref=\"PSR12\"/>\n</ruleset>\n",
            'phpstan.neon' => "parameters:\n    level: 6\n",
            'php-cs-fixer.dist.php' => "<?php\nreturn (new PhpCsFixer\\Config())->setRules(['@PSR12' => true]);\n",
        ];
        foreach ($files as $file => $contents) {
            $files[$file] = str_replace("\n", $eol, $contents);
            $this->put($root, $file, $files[$file]);
        }

        return $files;
    }

    /**
     * Executes a command using memory streams for precise output assertions.
     *
     * @param Application $app Application with the desired command collaborators.
     * @param string $root Consumer project root.
     * @param string $command Command to dispatch.
     * @return array{code: int, stdout: string, stderr: string} Exit code and both output streams.
     */
    private function runApp(Application $app, string $root, string $command = 'init'): array
    {
        $stdout = fopen('php://memory', 'w+');
        $stderr = fopen('php://memory', 'w+');
        $code = $app->run(['php-qa-scope', $command], $root, $stdout, $stderr);
        rewind($stdout);
        rewind($stderr);
        $out = stream_get_contents($stdout);
        $err = stream_get_contents($stderr);
        fclose($stdout);
        fclose($stderr);

        return ['code' => $code, 'stdout' => $out, 'stderr' => $err];
    }
}
