<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\InsertionLocator;

use RuntimeException;

/**
 * Resolves native insertion strategies by managed tool name.
 */
final class InsertionLocatorRegistry
{
    /**
     * Creates a registry with the provided insertion strategies.
     *
     * @param array<string, InsertionLocator> $locators Insertion strategies indexed by tool name.
     */
    public function __construct(private readonly array $locators)
    {
    }

    /**
     * Builds the registry for all supported native formats.
     *
     * @return self Registry containing the built-in insertion strategies.
     */
    public static function default(): self
    {
        return new self([
            'phpcs' => new PhpCodeSnifferInsertionLocator(),
            'phpstan' => new PhpStanInsertionLocator(),
            'php-cs-fixer' => new PhpCsFixerInsertionLocator(),
        ]);
    }

    /**
     * Returns the insertion strategy registered for a tool.
     *
     * @param string $tool Tool name to resolve.
     * @return InsertionLocator Insertion strategy for the requested tool.
     */
    public function get(string $tool): InsertionLocator
    {
        return $this->locators[$tool] ?? throw new RuntimeException("No insertion locator registered for '$tool'.");
    }
}
