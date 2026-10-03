<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Target;

use GustavoPeixoto\PhpQaScope\Block\BlockLocator;
use GustavoPeixoto\PhpQaScope\Renderer\RendererRegistry;
use GustavoPeixoto\PhpQaScope\Scope\ScopeCalculator;
use GustavoPeixoto\PhpQaScope\Scope\ScopeLoader;
use GustavoPeixoto\PhpQaScope\Scope\ToolScope;
use GustavoPeixoto\PhpQaScope\Tool;
use RuntimeException;

/**
 * Loads project scopes and inspects one native target at a time.
 */
final class TargetInspector
{
    /**
     * Creates an inspector with the supplied scope and native-target collaborators.
     *
     * @param ScopeLoader $loader Loader for project scope configuration.
     * @param ScopeCalculator $scopeCalculator Calculator for managed tool scopes.
     * @param RendererRegistry $renderers Registry of native renderers.
     * @param TargetRegistry $targets Registry of native target files.
     * @param BlockLocator $blockLocator Locator for managed marker blocks.
     */
    public function __construct(
        private readonly ScopeLoader $loader,
        private readonly ScopeCalculator $scopeCalculator,
        private readonly RendererRegistry $renderers,
        private readonly TargetRegistry $targets,
        private readonly BlockLocator $blockLocator,
    ) {
    }

    /**
     * Builds the inspector used by the application.
     *
     * @return self Inspector configured with built-in collaborators.
     */
    public static function default(): self
    {
        return new self(
            new ScopeLoader(),
            ScopeCalculator::default(),
            RendererRegistry::default(),
            TargetRegistry::default(),
            new BlockLocator(),
        );
    }

    /**
     * Validates configuration and calculates all managed scopes before file access.
     *
     * @param string $root Project root containing php-qa-scope.yml.
     * @return array<string, ToolScope> Effective scopes indexed by managed tool.
     */
    public function scopes(string $root): array
    {
        return $this->scopeCalculator->calculate($this->loader->load($root . '/php-qa-scope.yml'));
    }

    /**
     * Resolves the native file associated with a managed tool.
     *
     * @param Tool $tool Managed tool name.
     * @return TargetFile Native configuration target.
     */
    public function target(Tool $tool): TargetFile
    {
        return $this->targets->get($tool);
    }

    /**
     * Validates and compares a single native target without preparing replacement text.
     *
     * @param string $root Project root containing native QA configuration files.
     * @param Tool $tool Managed tool name.
     * @param ToolScope $scope Effective scope for the tool.
     * @return TargetInspection Current target content and comparison result.
     */
    public function inspect(string $root, Tool $tool, ToolScope $scope): TargetInspection
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

        $block = $this->blockLocator->locate($before, $target);
        $changed = str_replace("\r\n", "\n", $block->content) !== $expected;

        return new TargetInspection($target, $before, $block, $expected, $changed);
    }
}
