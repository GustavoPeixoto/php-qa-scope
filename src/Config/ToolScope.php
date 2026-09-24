<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Config;

/**
 * Holds include and exclude entries for a single QA tool.
 */
final readonly class ToolScope
{
    /**
     * Creates a scope for one tool.
     *
     * @param list<string> $include Include paths for the tool.
     * @param list<string> $exclude Exclude patterns for the tool.
     */
    public function __construct(
        public array $include,
        public array $exclude,
    ) {
    }
}
