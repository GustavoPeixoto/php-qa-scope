<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests;

use FilesystemIterator;
use PHPUnit\Framework\TestCase as PhpUnitTestCase;
use RecursiveDirectoryIterator;
use RecursiveIteratorIterator;
use Symfony\Component\Yaml\Yaml;

/**
 * Provides filesystem helpers shared by package tests.
 */
abstract class TestCase extends PhpUnitTestCase
{
    /** @var list<string> Temporary root directories scheduled for cleanup. */
    private array $temporaryRoots = [];

    /**
     * Removes temporary roots created by a test.
     */
    protected function tearDown(): void
    {
        foreach ($this->temporaryRoots as $root) {
            $this->removeTree($root);
        }

        $this->temporaryRoots = [];
        parent::tearDown();
    }

    /**
     * Creates a unique temporary project root.
     *
     * @param string $name Name segment used to identify the temporary root.
     * @return string Path to the created temporary root.
     */
    protected function tempRoot(string $name = 'project'): string
    {
        $root = sys_get_temp_dir() . '/php-qa-scope-' . $name . '-' . bin2hex(random_bytes(6));
        mkdir($root, 0777, true);
        $this->temporaryRoots[] = $root;

        return $root;
    }

    /**
     * Writes a minimal project fixture with php-qa-scope-managed config files.
     *
     * @param string $root Project root where fixture files are written.
     * @param array<string, mixed> $scope Scope configuration overrides.
     */
    protected function fixture(string $root, array $scope): void
    {
        $scope += [
            'include' => ['src', 'tests'],
            'exclude' => [],
            'tools' => [
                'phpstan' => ['include' => [], 'exclude' => []],
                'phpcs' => ['include' => [], 'exclude' => []],
                'php-cs-fixer' => ['include' => [], 'exclude' => []],
            ],
        ];

        $this->put($root, 'php-qa-scope.yml', Yaml::dump($scope, 5));
        $this->put($root, 'phpcs.xml', <<<'XML'
<?xml version="1.0"?>
<ruleset name="ScopeTest">
    <!-- outside -->
    <!-- php-qa-scope:start -->
    <!-- php-qa-scope:end -->
    <rule ref="PSR12"/>
</ruleset>

XML);
        $this->put($root, 'phpstan.neon', <<<'NEON'
parameters:
    level: 0
    tmpDir: cache
    # php-qa-scope:start
    # php-qa-scope:end

NEON);
        $this->put($root, 'php-cs-fixer.dist.php', <<<'PHP'
<?php
// outside
// php-qa-scope:start
// php-qa-scope:end
return (new PhpCsFixer\Config())->setRules(['@PSR12' => true])->setFinder($finder);

PHP);
    }

    /**
     * Writes a fixture file, creating parent directories as needed.
     *
     * @param string $root Project root containing the fixture.
     * @param string $path Relative file path to write.
     * @param string $content File content to write.
     */
    protected function put(string $root, string $path, string $content): void
    {
        $target = $root . '/' . $path;
        if (!is_dir(dirname($target))) {
            mkdir(dirname($target), 0777, true);
        }

        file_put_contents($target, $content);
    }

    /**
     * Runs a process in a working directory and captures its output.
     *
     * @param list<string> $arguments Process command and arguments.
     * @param string $cwd Working directory for the process.
     * @return array{code: int, stdout: string, stderr: string} Captured process result.
     */
    protected function process(array $arguments, string $cwd): array
    {
        $process = proc_open($arguments, [0 => ['pipe', 'r'], 1 => ['pipe', 'w'], 2 => ['pipe', 'w']], $pipes, $cwd);
        self::assertIsResource($process);
        fclose($pipes[0]);
        $stdout = stream_get_contents($pipes[1]);
        $stderr = stream_get_contents($pipes[2]);
        fclose($pipes[1]);
        fclose($pipes[2]);

        return ['code' => proc_close($process), 'stdout' => $stdout, 'stderr' => $stderr];
    }

    /**
     * Recursively removes a temporary root.
     *
     * @param string $root Directory tree to remove.
     */
    private function removeTree(string $root): void
    {
        if (!is_dir($root)) {
            return;
        }

        $iterator = new RecursiveIteratorIterator(
            new RecursiveDirectoryIterator($root, FilesystemIterator::SKIP_DOTS),
            RecursiveIteratorIterator::CHILD_FIRST,
        );

        foreach ($iterator as $entry) {
            if ($entry->isDir() && !$entry->isLink()) {
                rmdir($entry->getPathname());
            } else {
                unlink($entry->getPathname());
            }
        }

        rmdir($root);
    }
}
