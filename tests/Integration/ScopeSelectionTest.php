<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Integration;

use GustavoPeixoto\PhpQaScope\Tests\TestCase;

/**
 * Verifies generated scopes against the native tools' actual file discovery.
 */
final class ScopeSelectionTest extends TestCase
{
    /**
     * Verifies hidden paths, root-relative exclusions, and explicit includes across all tools.
     */
    public function testNativeToolsSelectTheSameFiles(): void
    {
        $root = $this->tempRoot('selection');
        $this->fixture($root, [
            'include' => ['src', 'tests', 'src/.hidden.php', 'src/.chosen'],
            'exclude' => ['src/Foo/**'],
        ]);
        $this->writePhpFiles($root);

        $expected = ['src/.chosen/Visible.php', 'src/.hidden.php', 'src/Visible.php', 'tests/Foo/Visible.php'];
        $this->assertNativeSelections($root, $expected);

        $this->fixture($root, [
            'include' => ['src', 'tests', 'src/.hidden.php', 'src/.chosen'],
            'exclude' => ['src/Foo/**', 'src/.chosen/**', 'src/.hidden.php'],
        ]);
        $this->assertNativeSelections($root, ['src/Visible.php', 'tests/Foo/Visible.php']);
    }

    /**
     * Writes files whose diagnostics identify exactly which paths each QA tool selected.
     *
     * @param string $root Temporary project root.
     */
    private function writePhpFiles(string $root): void
    {
        $paths = [
            'src/Visible.php',
            'src/.hidden.php',
            'src/.internal/Visible.php',
            'src/.chosen/Visible.php',
            'src/.chosen/.nested/Visible.php',
            'src/Foo/Visible.php',
            'tests/Foo/Visible.php',
            'other/Visible.php',
        ];

        foreach ($paths as $path) {
            $this->put($root, $path, "<?php\nscope_selection_missing_call( );\n");
        }
    }

    /**
     * Compares native PHPCS, PHPStan, and PHP-CS-Fixer selections with the expected paths.
     *
     * @param string $root Temporary project root.
     * @param list<string> $expected Expected project-relative paths.
     */
    private function assertNativeSelections(string $root, array $expected): void
    {
        $packageRoot = dirname(__DIR__, 2);
        $sync = $this->process([PHP_BINARY, $packageRoot . '/bin/php-qa-scope', 'sync'], $root);
        self::assertSame(0, $sync['code'], $sync['stderr']);

        $phpcs = $this->process([
            PHP_BINARY,
            $packageRoot . '/vendor/bin/phpcs',
            '--standard=' . $root . '/phpcs.xml',
            '--report=json',
        ], $root);
        $phpcsReport = json_decode($phpcs['stdout'], true, 512, JSON_THROW_ON_ERROR);
        self::assertIsArray($phpcsReport);
        $this->assertPaths($root, array_keys($phpcsReport['files']), $expected, 'PHPCS');

        $phpstan = $this->process([
            PHP_BINARY,
            '-r',
            <<<'PHP'
require 'phar://' . $argv[1] . '/vendor/phpstan/phpstan/phpstan.phar/vendor/autoload.php';
$parameters = (new PHPStan\DependencyInjection\NeonAdapter([]))->load($argv[2] . '/phpstan.neon')['parameters'];
$helper = new PHPStan\File\FileHelper($argv[2]);
$paths = array_map($helper->absolutizePath(...), $parameters['paths']);
$excludes = array_map(
    static fn ($path): string => $helper->absolutizePath(
        $path instanceof PHPStan\DependencyInjection\Neon\OptionalPath ? $path->path : $path,
    ),
    $parameters['excludePaths']['analyse'],
);
$finder = new PHPStan\File\FileFinder(
    new PHPStan\File\FileExcluder($helper, $excludes),
    $helper,
    ['php'],
    new PHPStan\File\DirectoryWalker(),
);
echo json_encode($finder->findFiles($paths)->getFiles(), JSON_THROW_ON_ERROR);
PHP,
            $packageRoot,
            $root,
        ], $root);
        self::assertSame(0, $phpstan['code'], $phpstan['stderr']);
        $phpstanPaths = json_decode($phpstan['stdout'], true, 512, JSON_THROW_ON_ERROR);
        self::assertIsArray($phpstanPaths);
        $this->assertPaths($root, $phpstanPaths, $expected, 'PHPStan');

        $fixer = $this->process([
            PHP_BINARY,
            '-r',
            <<<'PHP'
require $argv[2];
$config = require $argv[1];
foreach ($config->getFinder() as $file) {
    echo $file->getPathname(), "\n";
}
PHP,
            $root . '/php-cs-fixer.dist.php',
            $packageRoot . '/vendor/autoload.php',
        ], $root);
        self::assertSame(0, $fixer['code'], $fixer['stderr']);
        $this->assertPaths($root, array_filter(explode("\n", trim($fixer['stdout']))), $expected, 'PHP-CS-Fixer');
    }

    /**
     * Normalizes tool paths and compares their selected files.
     *
     * @param string $root Temporary project root.
     * @param array<int, string> $actual Tool-reported file paths.
     * @param list<string> $expected Expected project-relative paths.
     * @param string $tool Tool name for assertion context.
     */
    private function assertPaths(string $root, array $actual, array $expected, string $tool): void
    {
        $relative = array_map(static fn (string $path): string => substr($path, strlen($root) + 1), $actual);
        sort($relative);
        sort($expected);
        self::assertSame($expected, $relative, $tool);
    }
}
