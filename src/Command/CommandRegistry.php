<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Command;

use RuntimeException;

/**
 * Resolves CLI command names to command implementations.
 */
final class CommandRegistry
{
    /** @var array<string, Command> Commands indexed by CLI name. */
    private array $commands = [];

    /**
     * Registers the commands that may be dispatched.
     *
     * @param list<Command> $commands Command instances to index by name.
     */
    public function __construct(array $commands)
    {
        foreach ($commands as $command) {
            $this->commands[$command->name()] = $command;
        }
    }

    /**
     * Returns the command registered for a name.
     *
     * @param string $name Command name requested by the input.
     * @return Command Command implementation for the requested name.
     */
    public function get(string $name): Command
    {
        return $this->commands[$name] ?? throw new RuntimeException('Usage: php-qa-scope <sync|check>');
    }
}
