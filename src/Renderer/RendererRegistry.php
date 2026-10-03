<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Renderer;

use GustavoPeixoto\PhpQaScope\Tool;
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
            Tool::Phpcs->value => PhpCodeSnifferRenderer::default(),
            Tool::Phpstan->value => PhpStanRenderer::default(),
            Tool::PhpCsFixer->value => PhpCsFixerRenderer::default(),
        ]);
    }

    /**
     * Returns the renderer registered for a tool.
     *
     * @param Tool $tool Tool name to resolve.
     * @return Renderer Renderer for the requested tool.
     */
    public function get(Tool $tool): Renderer
    {
        return $this->renderers[$tool->value] ?? throw new RuntimeException(
            sprintf("No renderer registered for '%s'.", $tool->value),
        );
    }
}
