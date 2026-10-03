<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit\Composition;

use GustavoPeixoto\PhpQaScope\InsertionLocator\InsertionLocator;
use GustavoPeixoto\PhpQaScope\InsertionLocator\InsertionLocatorRegistry;
use GustavoPeixoto\PhpQaScope\Renderer\Renderer;
use GustavoPeixoto\PhpQaScope\Renderer\RendererRegistry;
use GustavoPeixoto\PhpQaScope\Scope\ToolScope;
use GustavoPeixoto\PhpQaScope\Target\TargetRegistry;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use GustavoPeixoto\PhpQaScope\Tool;
use RuntimeException;

/**
 * Covers independent default registries and authoritative custom implementations.
 */
final class NativeRegistryTest extends TestCase
{
    /**
     * Keeps registry objects and their entries independent across default calls.
     */
    public function testDefaultsAreIndependent(): void
    {
        foreach ([TargetRegistry::class, RendererRegistry::class, InsertionLocatorRegistry::class] as $type) {
            $first = $type::default();
            $second = $type::default();
            self::assertNotSame($first, $second);
            foreach (Tool::cases() as $tool) {
                self::assertNotSame($first->get($tool), $second->get($tool));
            }
        }
    }

    /**
     * Resolves the supplied renderer without affecting a default registry.
     */
    public function testUsesSuppliedRenderer(): void
    {
        $renderer = new class () implements Renderer {
            /**
             * Returns recognizable output for the supplied renderer contract.
             *
             * @param \GustavoPeixoto\PhpQaScope\Scope\ToolScope $scope Scope supplied by the caller.
             *
             * @return string Custom rendered block.
             */
            public function render(ToolScope $scope): string
            {
                return implode(',', $scope->include);
            }
        };
        $registry = new RendererRegistry([Tool::Phpcs->value => $renderer]);
        self::assertSame($renderer, $registry->get(Tool::Phpcs));
        self::assertSame('custom', $registry->get(Tool::Phpcs)->render(new ToolScope(['custom'], [])));
        self::assertNotSame($renderer, RendererRegistry::default()->get(Tool::Phpcs));
        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage("No renderer registered for 'phpstan'.");
        $registry->get(Tool::Phpstan);
    }

    /**
     * Resolves the supplied locator without substituting another registry's entry.
     */
    public function testUsesSuppliedLocator(): void
    {
        $locator = new class () implements InsertionLocator {
            /**
             * Uses the supplied content length as the custom insertion offset.
             *
             * @param string $contents Content inspected by the custom locator.
             *
             * @return int Custom insertion offset.
             */
            public function locate(string $contents): int
            {
                return strlen($contents);
            }
        };
        $registry = new InsertionLocatorRegistry([Tool::Phpcs->value => $locator]);
        self::assertSame($locator, $registry->get(Tool::Phpcs));
        self::assertSame(6, $registry->get(Tool::Phpcs)->locate('custom'));
        self::assertNotSame($locator, InsertionLocatorRegistry::default()->get(Tool::Phpcs));
        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage("No insertion locator registered for 'phpstan'.");
        $registry->get(Tool::Phpstan);
    }
}
