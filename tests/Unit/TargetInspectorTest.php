<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit;

use GustavoPeixoto\PhpQaScope\Config\ToolScope;
use GustavoPeixoto\PhpQaScope\Renderer\Renderer;
use GustavoPeixoto\PhpQaScope\Renderer\RendererRegistry;
use GustavoPeixoto\PhpQaScope\Sync\TargetInspector;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
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
        $before = (string) file_get_contents($root . '/phpcs.xml');
        $planner = TargetInspector::default();

        $inspection = $planner->inspect($root, 'phpcs', $planner->scopes($root)['phpcs']);

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
        $planner = TargetInspector::default();
        $scope = $planner->scopes($root)['phpcs'];
        $first = $planner->inspect($root, 'phpcs', $scope);
        $this->put($root, 'phpcs.xml', $first->replacement());

        $matching = $planner->inspect($root, 'phpcs', $scope);

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
            'tools' => ['phpstan' => ['include' => [], 'exclude' => []]],
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
        $planner = TargetInspector::default();

        $this->expectException(RuntimeException::class);
        $planner->inspect($root, 'phpstan', $planner->scopes($root)['phpstan']);
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
            'tools' => ['phpstan' => ['include' => [], 'exclude' => ['src/*.php']]],
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
        $failing = new class () implements Renderer {
            /**
             * Rejects one target to exercise local rendering failure.
             *
             * @param ToolScope $scope Scope supplied for the target.
             * @return string Rendered block, when available.
             */
            public function render(ToolScope $scope): string
            {
                throw new RuntimeException('render failed');
            }
        };
        $planner = new TargetInspector(renderers: new RendererRegistry(['phpcs' => $failing]));
        $scope = $planner->scopes($root)['phpcs'];

        $this->expectExceptionMessage('render failed');
        $planner->inspect($root, 'phpcs', $scope);
    }
}
