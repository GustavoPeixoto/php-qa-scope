<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Sync;

use GustavoPeixoto\PhpQaScope\Config\EffectiveScope;
use GustavoPeixoto\PhpQaScope\Config\ScopeLoader;
use GustavoPeixoto\PhpQaScope\Config\ToolScope;
use GustavoPeixoto\PhpQaScope\Renderer\RendererRegistry;
use RuntimeException;

/**
 * Loads project scopes and inspects one native target at a time.
 */
final class TargetInspector
{
    private readonly ScopeLoader $loader;
    private readonly EffectiveScope $effectiveScope;
    private readonly RendererRegistry $renderers;
    private readonly TargetRegistry $targets;
    private readonly ManagedBlock $managedBlock;

    /**
     * Creates an inspector with overridable collaborators for tests.
     *
     * @param ScopeLoader|null $loader Loader for project scope configuration.
     * @param EffectiveScope|null $effectiveScope Calculator for managed tool scopes.
     * @param RendererRegistry|null $renderers Registry of native renderers.
     * @param TargetRegistry|null $targets Registry of native target files.
     * @param ManagedBlock|null $managedBlock Locator for managed marker blocks.
     */
    public function __construct(
        ?ScopeLoader $loader = null,
        ?EffectiveScope $effectiveScope = null,
        ?RendererRegistry $renderers = null,
        ?TargetRegistry $targets = null,
        ?ManagedBlock $managedBlock = null,
    ) {
        $this->loader = $loader ?? new ScopeLoader();
        $this->effectiveScope = $effectiveScope ?? new EffectiveScope();
        $this->renderers = $renderers ?? RendererRegistry::default();
        $this->targets = $targets ?? new TargetRegistry();
        $this->managedBlock = $managedBlock ?? new ManagedBlock();
    }

    /**
     * Builds the inspector used by the application.
     *
     * @return self Inspector configured with built-in collaborators.
     */
    public static function default(): self
    {
        return new self();
    }

    /**
     * Validates configuration and calculates all managed scopes before file access.
     *
     * @param string $root Project root containing php-qa-scope.yml.
     * @return array<string, ToolScope> Effective scopes indexed by managed tool.
     */
    public function scopes(string $root): array
    {
        return $this->effectiveScope->calculate($this->loader->load($root . '/php-qa-scope.yml'));
    }

    /**
     * Resolves the native file associated with a managed tool.
     *
     * @param string $tool Managed tool name.
     * @return TargetFile Native configuration target.
     */
    public function target(string $tool): TargetFile
    {
        return $this->targets->get($tool);
    }

    /**
     * Validates and compares a single native target without preparing replacement text.
     *
     * @param string $root Project root containing native QA configuration files.
     * @param string $tool Managed tool name.
     * @param ToolScope $scope Effective scope for the tool.
     * @return TargetInspection Current target content and comparison result.
     */
    public function inspect(string $root, string $tool, ToolScope $scope): TargetInspection
    {
        $target = $this->target($tool);
        $expected = $this->renderers->get($tool)->render($scope);
        $path = $root . '/' . $target->path;

        if (is_link($path)) {
            throw new RuntimeException("$target->path: managed configuration files cannot be symbolic links.");
        }

        $before = is_file($path) ? file_get_contents($path) : false;
        if ($before === false) {
            throw new RuntimeException("$target->path: could not read the configuration.");
        }

        $block = $this->managedBlock->locate($before, $target);
        $changed = str_replace("\r\n", "\n", $block->content) !== $expected;

        return new TargetInspection($target, $before, $block, $expected, $changed);
    }
}
