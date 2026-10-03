<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit;

use GustavoPeixoto\PhpQaScope\Scope\ScopeInitializer;
use GustavoPeixoto\PhpQaScope\Scope\ScopeLoader;
use GustavoPeixoto\PhpQaScope\Target\TargetRegistry;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use GustavoPeixoto\PhpQaScope\Tool;
use RuntimeException;

/**
 * Covers generated YAML defaults and create-only destination safeguards.
 */
final class ScopeInitializerTest extends TestCase
{
    /**
     * Creates provided tool defaults without discovering native files or requiring a source directory.
     */
    public function testCreatesDefaultsForProvidedTools(): void
    {
        $root = $this->tempRoot();
        $tools = ['phpstan' => TargetRegistry::default()->get(Tool::Phpstan)];
        (new ScopeInitializer())->create($root, $tools);
        $config = (new ScopeLoader())->load($root . '/php-qa-scope.yml');

        self::assertSame(['src'], $config->include);
        self::assertSame([], $config->exclude);
        self::assertSame([Tool::Phpstan], $config->managedTools());
        self::assertSame([], $config->tool(Tool::Phpstan)->include);
        self::assertSame([], $config->tool(Tool::Phpstan)->exclude);
        self::assertSame(
            "include:\n  - src\nexclude: []\ntools:\n  phpstan:\n    include: []\n    exclude: []\n",
            file_get_contents($root . '/php-qa-scope.yml'),
        );
        self::assertDirectoryDoesNotExist($root . '/src');
    }

    /**
     * Creates all three detected tools with empty local scope arrays.
     */
    public function testCreatesAllToolDefaults(): void
    {
        $root = $this->tempRoot();
        foreach (['phpcs.xml', 'phpstan.neon', 'php-cs-fixer.dist.php'] as $file) {
            $this->put($root, $file, 'configuration');
        }
        (new ScopeInitializer())->create($root, TargetRegistry::default()->discover($root));
        $config = (new ScopeLoader())->load($root . '/php-qa-scope.yml');

        self::assertSame(Tool::cases(), $config->managedTools());
        foreach ($config->managedTools() as $tool) {
            self::assertSame([], $config->tool($tool)->include);
            self::assertSame([], $config->tool($tool)->exclude);
        }
    }

    /**
     * Preserves an existing YAML destination without replacing its bytes or inode.
     */
    public function testCreationDoesNotOverwriteExistingYaml(): void
    {
        $root = $this->tempRoot();
        self::assertFileDoesNotExist($root . '/php-qa-scope.yml');
        $this->put($root, 'php-qa-scope.yml', 'concurrent configuration');
        $inode = fileinode($root . '/php-qa-scope.yml');

        (new ScopeInitializer())->create($root, []);

        self::assertSame('concurrent configuration', file_get_contents($root . '/php-qa-scope.yml'));
        clearstatcache(true, $root . '/php-qa-scope.yml');
        self::assertSame($inode, fileinode($root . '/php-qa-scope.yml'));
        self::assertSame([], glob($root . '/.php-qa-scope-*'));
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

            try {
                (new ScopeInitializer())->create($root, []);
                self::fail('YAML links must be rejected.');
            } catch (RuntimeException $error) {
                self::assertStringContainsString('symbolic link', $error->getMessage());
            }

            self::assertTrue(is_link($root . '/php-qa-scope.yml'));
            self::assertSame('parameters:', file_get_contents($root . '/phpstan.neon'));
        }
    }

    /**
     * Reports an inaccessible creation destination without leaving a temporary file.
     */
    public function testCreationFailureLeavesNoTemporaryFile(): void
    {
        $root = $this->tempRoot();

        try {
            (new ScopeInitializer())->create($root . '/missing', []);
            self::fail('A nonexistent destination must fail.');
        } catch (RuntimeException $error) {
            self::assertStringContainsString('could not create', $error->getMessage());
        }

        self::assertSame([], glob($root . '/.php-qa-scope-*'));
    }
}
