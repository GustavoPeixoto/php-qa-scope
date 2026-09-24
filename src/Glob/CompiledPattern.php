<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Glob;

/**
 * Carries compiled representations of a supported exclude pattern.
 */
final readonly class CompiledPattern
{
    /**
     * Creates a compiled pattern for renderer-specific consumers.
     *
     * @param string $regex Regular expression fragment used by renderers and matchers.
     * @param list<string> $phpStanPaths PHPStan exclude paths derived from the pattern.
     * @param bool $optionalForPhpStan Whether PHPStan should treat the exclude as optional.
     */
    public function __construct(
        public string $regex,
        public array $phpStanPaths,
        public bool $optionalForPhpStan = false,
    ) {
    }
}
