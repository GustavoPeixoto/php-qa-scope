<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Integration;

use GustavoPeixoto\PhpQaScope\Application;
use GustavoPeixoto\PhpQaScope\Cli\ExitCode;
use GustavoPeixoto\PhpQaScope\Console\Console;
use GustavoPeixoto\PhpQaScope\Console\ConsoleWriter;
use GustavoPeixoto\PhpQaScope\Scope\ScopeCalculator;
use GustavoPeixoto\PhpQaScope\Scope\ScopeLoader;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;

/**
 * Covers initialization of projects that already contain scope configuration.
 */
final class InitScopeSetupIntegrationTest extends TestCase
{
    /**
     * Uses custom effective scopes without rewriting existing YAML or adding tools.
     */
    public function testPreservesExistingYamlAndToolSelection(): void
    {
        $root = $this->tempRoot();
        $yaml = "# consumer comment\ninclude: [app]\nexclude: []\ntools:\n"
            . "  phpstan:\n    include: [tests]\n    exclude: ['app/legacy/**']\n";
        $this->put($root, 'php-qa-scope.yml', $yaml);
        foreach (['phpcs.xml', 'phpstan.neon', 'php-cs-fixer.dist.php'] as $file) {
            $this->put($root, $file, 'original native configuration');
        }
        $this->put($root, 'phpstan.neon', "parameters:\n    level: 6\n");
        $inode = fileinode($root . '/php-qa-scope.yml');
        [$code] = $this->runApp(Application::default(), ['php-qa-scope', 'init'], $root);
        self::assertSame(ExitCode::SUCCESS, $code);
        $scopes = ScopeCalculator::default()->calculate((new ScopeLoader())->load($root . '/php-qa-scope.yml'));

        self::assertSame(['phpstan'], array_keys($scopes));
        self::assertSame(['app', 'tests'], $scopes['phpstan']->include);
        self::assertSame(['app/legacy/**'], $scopes['phpstan']->exclude);
        self::assertSame($yaml, file_get_contents($root . '/php-qa-scope.yml'));
        clearstatcache(true, $root . '/php-qa-scope.yml');
        self::assertSame($inode, fileinode($root . '/php-qa-scope.yml'));
    }

    /**
     * Leaves the currently valid empty managed-tools configuration unchanged.
     */
    public function testPreservesAnEmptyToolsMap(): void
    {
        $root = $this->tempRoot();
        $yaml = "include: [src]\nexclude: []\ntools: {}\n";
        $this->put($root, 'phpstan.neon', 'parameters:');
        $this->put($root, 'php-qa-scope.yml', $yaml);

        [$code, $stdout, $stderr] = $this->runApp(Application::default(), ['php-qa-scope', 'init'], $root);
        self::assertSame(ExitCode::SUCCESS, $code);
        self::assertSame('', $stdout);
        self::assertSame('', $stderr);
        self::assertSame($yaml, file_get_contents($root . '/php-qa-scope.yml'));
    }

    /**
     * Fails invalid or unreadable YAML without touching native files.
     */
    public function testInvalidOrUnreadableYamlStopsSetup(): void
    {
        foreach (["include: [\n", "include: []\nexclude: []\ntools: {}\n", null] as $yaml) {
            $root = $this->tempRoot();
            $this->put($root, 'phpstan.neon', 'original native configuration');
            if ($yaml === null) {
                mkdir($root . '/php-qa-scope.yml');
            } else {
                $this->put($root, 'php-qa-scope.yml', $yaml);
            }

            [$code] = $this->runApp(Application::default(), ['php-qa-scope', 'init'], $root);
            self::assertSame(ExitCode::ERROR, $code);
            self::assertSame('original native configuration', file_get_contents($root . '/phpstan.neon'));
            if ($yaml !== null) {
                self::assertSame($yaml, file_get_contents($root . '/php-qa-scope.yml'));
            }
        }
    }

    /**
     * Rejects YAML links, including dangling links, without replacing them.
     */
    public function testRejectsYamlSymbolicLinks(): void
    {
        foreach ([false, true] as $dangling) {
            $root = $this->tempRoot();
            $this->put($root, 'phpstan.neon', 'parameters:');
            if (!$dangling) {
                $this->put($root, 'actual.yml', 'original');
            }
            symlink($root . '/actual.yml', $root . '/php-qa-scope.yml');

            [$code, , $stderr] = $this->runApp(Application::default(), ['php-qa-scope', 'init'], $root);
            self::assertSame(ExitCode::ERROR, $code);
            self::assertStringContainsString('symbolic link', $stderr);
            self::assertTrue(is_link($root . '/php-qa-scope.yml'));
            self::assertSame('parameters:', file_get_contents($root . '/phpstan.neon'));
        }
    }

    /**
     * Still requires supported native files when scope YAML already exists.
     */
    public function testExistingYamlStillRequiresNativeConfiguration(): void
    {
        $root = $this->tempRoot();
        $yaml = "include: [src]\nexclude: []\ntools: {}\n";
        $this->put($root, 'php-qa-scope.yml', $yaml);
        $inode = fileinode($root . '/php-qa-scope.yml');

        [$code, , $stderr] = $this->runApp(Application::default(), ['php-qa-scope', 'init'], $root);

        self::assertSame(ExitCode::ERROR, $code);
        self::assertStringContainsString('No supported QA configuration', $stderr);
        self::assertSame($yaml, file_get_contents($root . '/php-qa-scope.yml'));
        clearstatcache(true, $root . '/php-qa-scope.yml');
        self::assertSame($inode, fileinode($root . '/php-qa-scope.yml'));
        self::assertSame([], glob($root . '/.php-qa-scope-*'));
    }

    /**
     * Stops before creating YAML when no supported native configuration exists.
     */
    public function testNoNativeFilesDoesNotCreateYaml(): void
    {
        $root = $this->tempRoot();

        [$code, , $stderr] = $this->runApp(Application::default(), ['php-qa-scope', 'init'], $root);

        self::assertSame(ExitCode::ERROR, $code);
        self::assertStringContainsString('No supported QA configuration', $stderr);
        self::assertFileDoesNotExist($root . '/php-qa-scope.yml');
        self::assertSame([], glob($root . '/.php-qa-scope-*'));
    }

    /**
     * Reports missing native configurations before validating YAML links.
     */
    public function testMissingNativeConfigurationTakesPriorityOverYamlSymlinks(): void
    {
        foreach ([false, true] as $dangling) {
            $root = $this->tempRoot();
            if (!$dangling) {
                $this->put($root, 'actual.yml', 'consumer configuration');
            }
            symlink($root . '/actual.yml', $root . '/php-qa-scope.yml');

            [$code, , $stderr] = $this->runApp(Application::default(), ['php-qa-scope', 'init'], $root);

            self::assertSame(ExitCode::ERROR, $code);
            self::assertStringNotContainsString('symbolic link', $stderr);
            self::assertStringContainsString('No supported QA configuration', $stderr);
            self::assertTrue(is_link($root . '/php-qa-scope.yml'));
            self::assertSame([], glob($root . '/.php-qa-scope-*'));
            if (!$dangling) {
                self::assertSame('consumer configuration', file_get_contents($root . '/actual.yml'));
            }
        }
    }

    /**
     * Executes a command while capturing its status and output streams.
     *
     * @param Application $app Application containing the command registry.
     * @param list<string> $argv Arguments selecting the command.
     * @param string $root Temporary consumer project root.
     * @return array{int, string, string} Exit code, standard output, and standard error.
     */
    private function runApp(Application $app, array $argv, string $root): array
    {
        $stdout = fopen('php://memory', 'w+');
        $stderr = fopen('php://memory', 'w+');

        try {
            $code = $app->run($argv, new Console(new ConsoleWriter($stdout, $stderr)), $root);
            rewind($stdout);
            rewind($stderr);

            return [$code, (string) stream_get_contents($stdout), (string) stream_get_contents($stderr)];
        } finally {
            fclose($stdout);
            fclose($stderr);
        }
    }
}
