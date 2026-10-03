<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit\Target;

use GustavoPeixoto\PhpQaScope\Block\BlockLocator;
use GustavoPeixoto\PhpQaScope\Renderer\Renderer;
use GustavoPeixoto\PhpQaScope\Renderer\RendererRegistry;
use GustavoPeixoto\PhpQaScope\Scope\ScopeCalculator;
use GustavoPeixoto\PhpQaScope\Scope\ScopeLoader;
use GustavoPeixoto\PhpQaScope\Scope\ToolScope;
use GustavoPeixoto\PhpQaScope\Target\TargetInspector;
use GustavoPeixoto\PhpQaScope\Target\TargetRegistry;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use GustavoPeixoto\PhpQaScope\Tool;
use RuntimeException;
use Symfony\Component\Yaml\Yaml;

/**
 * Covers command-wide scope loading and independent target inspection.
 */
final class TargetInspectorTest extends TestCase
{
    /**
     * Verifies inspection reports drift without writing or holding replacement text.
     */
    public function testInspectsDivergentTargetWithoutReplacement(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, []);
        $before = (string)file_get_contents($root . '/phpcs.xml');
        $inspector = TargetInspector::default();

        $inspection = $inspector->inspect($root, Tool::Phpcs, $inspector->scopes($root)['phpcs']);

        self::assertTrue($inspection->changed);
        self::assertArrayNotHasKey('after', get_object_vars($inspection));
        self::assertSame($before, file_get_contents($root . '/phpcs.xml'));
    }

    /**
     * Verifies a matching target does not require a replacement file.
     */
    public function testInspectsMatchingTargetWithoutReplacement(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, []);
        $inspector = TargetInspector::default();
        $scope = $inspector->scopes($root)['phpcs'];
        $first = $inspector->inspect($root, Tool::Phpcs, $scope);
        $this->put($root, 'phpcs.xml', $first->replacement());

        $matching = $inspector->inspect($root, Tool::Phpcs, $scope);

        self::assertFalse($matching->changed);
        self::assertArrayNotHasKey('after', get_object_vars($matching));
    }

    /**
     * Verifies absent tools are skipped without resolving their native targets.
     */
    public function testSkipsAbsentToolsWithoutAccessingTargets(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, [
            'tools' => [
                'phpstan' => [
                    'include' => [],
                    'exclude' => [],
                ],
            ],
        ]);
        unlink($root . '/phpcs.xml');
        unlink($root . '/php-cs-fixer.dist.php');

        $scopes = TargetInspector::default()->scopes($root);

        self::assertSame(['phpstan'], array_keys($scopes));
    }

    /**
     * Verifies a missing native target fails only its inspection.
     */
    public function testListedToolRequiresNativeTarget(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, []);
        unlink($root . '/phpstan.neon');
        $inspector = TargetInspector::default();

        $this->expectException(RuntimeException::class);
        $inspector->inspect($root, Tool::Phpstan, $inspector->scopes($root)['phpstan']);
    }

    /**
     * Verifies invalid scope patterns fail before native inspection.
     */
    public function testRejectsInvalidToolPatternDuringScopeLoading(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, []);
        $this->put($root, 'php-qa-scope.yml', Yaml::dump([
            'include' => ['src'],
            'exclude' => [],
            'tools' => [
                'phpstan' => [
                    'include' => [],
                    'exclude' => ['src/*.php'],
                ],
            ],
        ], 5));

        $this->expectException(RuntimeException::class);
        TargetInspector::default()->scopes($root);
    }

    /**
     * Verifies rendering failure is limited to the inspected target.
     */
    public function testRenderingFailureIsTargetLocal(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, []);
        $failingRenderer = new class () implements Renderer {
            /**
             * Rejects one target to exercise local rendering failure.
             *
             * @param \GustavoPeixoto\PhpQaScope\Scope\ToolScope $scope Scope supplied for the target.
             *
             * @return string Rendered block, when available.
             */
            public function render(ToolScope $scope): string
            {
                throw new RuntimeException('render failed');
            }
        };
        $inspector = new TargetInspector(
            renderers: new RendererRegistry(['phpcs' => $failingRenderer]),
            loader: new ScopeLoader(),
            scopeCalculator: ScopeCalculator::default(),
            targets: TargetRegistry::default(),
            blockLocator: new BlockLocator(),
        );
        $scope = $inspector->scopes($root)['phpcs'];

        $this->expectExceptionMessage('render failed');
        $inspector->inspect($root, Tool::Phpcs, $scope);
    }
}
