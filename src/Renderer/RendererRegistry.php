<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Renderer;

use RuntimeException;

/**
 * Resolves native tool names to managed block renderers.
 */
final class RendererRegistry
{
    /**
     * Creates a registry from renderer instances.
     *
     * @param array<string, Renderer> $renderers Renderers indexed by tool name.
     */
    public function __construct(private readonly array $renderers)
    {
    }

    /**
     * Builds the default renderer registry for supported tools.
     *
     * @return self Registry containing all built-in renderers.
     */
    public static function default(): self
    {
        return new self([
            'phpcs' => new PhpCodeSnifferRenderer(),
            'phpstan' => new PhpStanRenderer(),
            'php-cs-fixer' => new PhpCsFixerRenderer(),
        ]);
    }

    /**
     * Returns the renderer registered for a tool.
     *
     * @param string $tool Tool name to resolve.
     * @return Renderer Renderer for the requested tool.
     */
    public function get(string $tool): Renderer
    {
        return $this->renderers[$tool] ?? throw new RuntimeException("No renderer registered for '$tool'.");
    }
}
