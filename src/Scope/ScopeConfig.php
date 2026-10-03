<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Scope;

use GustavoPeixoto\PhpQaScope\Tool;

/**
 * Holds the loaded php-qa-scope configuration.
 */
final readonly class ScopeConfig
{
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
        foreach (array_keys($tools) as $tool) {
            if (Tool::tryFrom((string) $tool) === null) {
                throw new \RuntimeException("tools: unknown key '$tool'.");
            }
        }
    }

    /**
     * Returns the tools explicitly managed by the configuration.
     *
     * @return list<Tool> Managed tool identities.
     */
    public function managedTools(): array
    {
        $tools = [];
        foreach (array_keys($this->tools) as $tool) {
            $tools[] = Tool::from($tool);
        }

        return $tools;
    }

    /**
     * Returns the scope configured for one managed tool.
     *
     * @param Tool $tool Tool name to resolve.
     * @return ToolScope Scope configured for the requested tool.
     */
    public function tool(Tool $tool): ToolScope
    {
        return $this->tools[$tool->value] ?? throw new \RuntimeException(
            sprintf("Tool '%s' is not managed.", $tool->value),
        );
    }
}
