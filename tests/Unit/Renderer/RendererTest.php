<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit\Renderer;

use GustavoPeixoto\PhpQaScope\Renderer\PhpCodeSnifferRenderer;
use GustavoPeixoto\PhpQaScope\Renderer\PhpCsFixerRenderer;
use GustavoPeixoto\PhpQaScope\Renderer\PhpStanRenderer;
use GustavoPeixoto\PhpQaScope\Renderer\RendererRegistry;
use GustavoPeixoto\PhpQaScope\Scope\ToolScope;
use GustavoPeixoto\PhpQaScope\Target\TargetRegistry;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use GustavoPeixoto\PhpQaScope\Tool;

/**
 * Covers native configuration renderers and their registries.
 */
final class RendererTest extends TestCase
{
    /**
     * Verifies PHPCS managed block rendering.
     */
    public function testRendersPhpCodeSnifferBlock(): void
    {
        $block = PhpCodeSnifferRenderer::default()->render(new ToolScope(['src', 'tests'], ['tests/fixtures/**']));

        self::assertStringContainsString('    <file>.</file>', $block);
        self::assertStringContainsString('    <arg name="extensions" value="php"/>', $block);
        self::assertStringContainsString('tests/fixtures', $block);
    }

    /**
     * Verifies PHPStan managed block rendering.
     */
    public function testRendersPhpStanBlock(): void
    {
        $block = PhpStanRenderer::default()->render(new ToolScope(['src', 'tests'], ['src/Compatibility.php']));

        self::assertSame(<<<'NEON'
    paths:
        - 'src'
        - 'tests'
    excludePaths:
        analyse:
            - 'src/Compatibility.php' (?)

NEON, $block);
    }

    /**
     * Verifies PHP-CS-Fixer managed block rendering.
     */
    public function testRendersPhpCsFixerBlock(): void
    {
        $block = PhpCsFixerRenderer::default()->render(
            new ToolScope(['scripts/single.php', 'src'], ['**/*Generated.php']),
        );

        self::assertStringContainsString("->in([\n        __DIR__ . '/src',\n    ]);", $block);
        self::assertStringContainsString("new SplFileInfo(__DIR__ . '/scripts/single.php'),", $block);
        self::assertStringContainsString('CallbackFilterIterator', $block);
        self::assertStringContainsString('Generated\\\\.php', $block);
    }

    /**
     * Verifies default renderer and target registrations.
     */
    public function testRegistersRenderersAndNativeTargets(): void
    {
        $renderers = RendererRegistry::default();
        $targets = TargetRegistry::default();

        self::assertInstanceOf(PhpCodeSnifferRenderer::class, $renderers->get(Tool::Phpcs));
        self::assertSame('phpcs.xml', $targets->get(Tool::Phpcs)->path);
        self::assertSame('phpstan.neon', $targets->get(Tool::Phpstan)->path);
        self::assertSame('php-cs-fixer.dist.php', $targets->get(Tool::PhpCsFixer)->path);
        self::assertSame('<!-- php-qa-scope:%s -->', $targets->get(Tool::Phpcs)->marker);
        self::assertSame('# php-qa-scope:%s', $targets->get(Tool::Phpstan)->marker);
        self::assertSame('// php-qa-scope:%s', $targets->get(Tool::PhpCsFixer)->marker);
    }
}
