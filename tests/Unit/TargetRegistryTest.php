<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit;

use GustavoPeixoto\PhpQaScope\Target\TargetRegistry;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use RuntimeException;

/**
 * Covers root-only discovery against the shared native target definitions.
 */
final class TargetRegistryTest extends TestCase
{
    /**
     * Discovers every nonempty combination in a deterministic registry order.
     */
    public function testDiscoversEveryToolCombination(): void
    {
        $registry = new TargetRegistry();
        $tools = ['phpcs', 'phpstan', 'php-cs-fixer'];
        for ($mask = 1; $mask < 8; ++$mask) {
            $root = $this->tempRoot();
            $expected = [];
            foreach ($tools as $index => $tool) {
                if (($mask & (1 << $index)) !== 0) {
                    $this->put($root, $registry->get($tool)->path, 'configuration');
                    $expected[] = $tool;
                }
            }

            self::assertSame($expected, array_keys($registry->discover($root)));
        }
    }

    /**
     * Ignores alternate filenames and configurations outside the root.
     */
    public function testRejectsAlternateAndNestedConfigurations(): void
    {
        $root = $this->tempRoot();
        foreach (['phpcs.xml.dist', 'phpstan.neon.dist', '.php-cs-fixer.dist.php', 'config/phpcs.xml'] as $path) {
            $this->put($root, $path, 'configuration');
        }
        mkdir($root . '/phpstan.neon');

        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage('No supported QA configuration');
        (new TargetRegistry())->discover($root);
    }

    /**
     * Rejects an empty project rather than managing an arbitrary tool set.
     */
    public function testRejectsAnEmptyRoot(): void
    {
        $this->expectException(RuntimeException::class);
        (new TargetRegistry())->discover($this->tempRoot());
    }
}
