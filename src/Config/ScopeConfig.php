<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Config;

/**
 * Holds the loaded php-qa-scope configuration.
 */
final readonly class ScopeConfig
{
    public const TOOLS = ['phpcs', 'phpstan', 'php-cs-fixer'];

    /**
     * Creates a configuration value object.
     *
     * @param list<string> $include Global include paths.
     * @param list<string> $exclude Global exclude patterns.
     * @param array<string, ToolScope> $tools Tool-specific scope configuration indexed by tool name.
     */
    public function __construct(
        public array $include,
        public array $exclude,
        public array $tools,
    ) {
    }

    /**
     * Returns the tools explicitly managed by the configuration.
     *
     * @return list<string> Managed tool names.
     */
    public function managedTools(): array
    {
        return array_keys($this->tools);
    }

    /**
     * Returns the scope configured for one managed tool.
     *
     * @param string $tool Tool name to resolve.
     * @return ToolScope Scope configured for the requested tool.
     */
    public function tool(string $tool): ToolScope
    {
        return $this->tools[$tool] ?? throw new \RuntimeException("Tool '$tool' is not managed.");
    }
}
