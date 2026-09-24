<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Cli;

use RuntimeException;

/**
 * Represents validated command-line input for a php-qa-scope run.
 */
final readonly class Input
{
    /**
     * Creates input from the selected command and project root.
     *
     * @param string $command Command name requested by the user.
     * @param string $root Project root where configuration files are resolved.
     */
    public function __construct(
        public string $command,
        public string $root,
    ) {
    }

    /**
     * Parses command-line arguments into package input.
     *
     * @param list<string> $argv Command-line arguments including the executable name.
     * @param string|null $root Project root override, or null to use the current working directory.
     * @return self Parsed input ready for command dispatch.
     */
    public static function fromArgv(array $argv, ?string $root = null): self
    {
        if (count($argv) !== 2) {
            throw new RuntimeException('Usage: php-qa-scope <sync|check>');
        }

        $resolvedRoot = $root ?? getcwd();
        if ($resolvedRoot === false) {
            throw new RuntimeException('Could not determine the project root.');
        }

        return new self($argv[1], $resolvedRoot);
    }
}
