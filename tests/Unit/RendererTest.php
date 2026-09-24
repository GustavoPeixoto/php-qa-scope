<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit;

use GustavoPeixoto\PhpQaScope\Config\ToolScope;
use GustavoPeixoto\PhpQaScope\Renderer\PhpCodeSnifferRenderer;
use GustavoPeixoto\PhpQaScope\Renderer\PhpCsFixerRenderer;
use GustavoPeixoto\PhpQaScope\Renderer\PhpStanRenderer;
use GustavoPeixoto\PhpQaScope\Renderer\RendererRegistry;
use GustavoPeixoto\PhpQaScope\Sync\TargetRegistry;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;

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
        $block = (new PhpCodeSnifferRenderer())->render(new ToolScope(['src', 'tests'], ['tests/fixtures/**']));

        self::assertStringContainsString('    <file>.</file>', $block);
        self::assertStringContainsString('    <arg name="extensions" value="php"/>', $block);
        self::assertStringContainsString('tests/fixtures', $block);
    }

    /**
     * Verifies PHPStan managed block rendering.
     */
    public function testRendersPhpStanBlock(): void
    {
        $block = (new PhpStanRenderer())->render(new ToolScope(['src', 'tests'], ['src/Compatibility.php']));

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
        $block = (new PhpCsFixerRenderer())->render(
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
        $targets = new TargetRegistry();

        self::assertInstanceOf(PhpCodeSnifferRenderer::class, $renderers->get('phpcs'));
        self::assertSame('phpcs.xml', $targets->get('phpcs')->path);
        self::assertSame('phpstan.neon', $targets->get('phpstan')->path);
        self::assertSame('php-cs-fixer.dist.php', $targets->get('php-cs-fixer')->path);
        self::assertSame('<!-- php-qa-scope:%s -->', $targets->get('phpcs')->marker);
        self::assertSame('# php-qa-scope:%s', $targets->get('phpstan')->marker);
        self::assertSame('// php-qa-scope:%s', $targets->get('php-cs-fixer')->marker);
    }
}
