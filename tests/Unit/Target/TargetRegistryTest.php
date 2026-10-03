<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit\Target;

use GustavoPeixoto\PhpQaScope\Target\TargetFile;
use GustavoPeixoto\PhpQaScope\Target\TargetRegistry;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use GustavoPeixoto\PhpQaScope\Tool;
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
        $registry = TargetRegistry::default();
        $tools = [
            'phpcs',
            'phpstan',
            'php-cs-fixer',
        ];
        for ($mask = 1; $mask < 8; ++$mask) {
            $root = $this->tempRoot();
            $expected = [];
            foreach ($tools as $index => $tool) {
                if (!(($mask & (1 << $index)) !== 0)) {
                    continue;
                }

                $this->put($root, $registry->get(Tool::from($tool))->path, 'configuration');
                $expected[] = $tool;
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
        TargetRegistry::default()->discover($root);
    }

    /**
     * Rejects an empty project rather than managing an arbitrary tool set.
     */
    public function testRejectsAnEmptyRoot(): void
    {
        $this->expectException(RuntimeException::class);
        TargetRegistry::default()->discover($this->tempRoot());
    }

    /**
     * Discovers the caller's supplied path rather than replacing it with a built-in target.
     */
    public function testUsesCustomTargetDefinition(): void
    {
        $root = $this->tempRoot();
        $target = new TargetFile(Tool::Phpstan, 'custom.neon', '# scope:%s', '');
        $registry = new TargetRegistry([Tool::Phpstan->value => $target]);
        $this->put($root, 'custom.neon', 'configuration');

        self::assertSame($target, $registry->get(Tool::Phpstan));
        self::assertSame(['phpstan' => $target], $registry->discover($root));
        self::assertSame('phpstan.neon', TargetRegistry::default()->get(Tool::Phpstan)->path);
    }

    /**
     * Rejects inconsistent mappings before a target can be discovered or written.
     */
    public function testRejectsMismatchedTargetIdentity(): void
    {
        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage("Target key 'phpcs' does not match tool 'phpstan'.");
        new TargetRegistry(['phpcs' => new TargetFile(Tool::Phpstan, 'custom.neon', '# scope:%s', '')]);
    }

    /**
     * Reports missing registrations without looking up a built-in fallback.
     */
    public function testRejectsMissingRegistration(): void
    {
        $registry = new TargetRegistry([]);
        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage("No target registered for 'phpstan'.");
        $registry->get(Tool::Phpstan);
    }
}
