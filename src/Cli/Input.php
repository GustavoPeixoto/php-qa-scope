<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Cli;

use RuntimeException;

/**
 * Holds parsed command-line values before command registry validation.
 */
final readonly class Input
{
    /**
     * Creates input from the selected command and project root.
     *
     * @param string $command Parsed command name, or an empty string when absent.
     * @param string $root Project root where configuration files are resolved.
     */
    public function __construct(
        public string $command,
        public string $root,
    ) {
    }

    /**
     * Parses a command name and root while rejecting extra arguments.
     *
     * @param list<string> $argv Command-line arguments including the executable name.
     * @param string $usage Registry-derived usage text for extra-argument errors.
     * @param string|null $root Project root override, or null to use the current working directory.
     *
     * @return self Parsed input ready for command dispatch.
     */
    public static function fromArgv(array $argv, string $usage, ?string $root = null): self
    {
        if (count($argv) > 2) {
            throw new RuntimeException($usage);
        }

        $resolvedRoot = $root ?? getcwd();
        if ($resolvedRoot === false) {
            throw new RuntimeException('Could not determine the project root.');
        }

        return new self($argv[1] ?? '', $resolvedRoot);
    }
}
