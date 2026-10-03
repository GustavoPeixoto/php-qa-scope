<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Command;

use RuntimeException;

/**
 * Resolves CLI command names to command implementations.
 */
final class CommandRegistry
{
    /** @var array<string, \GustavoPeixoto\PhpQaScope\Command\Command> Commands indexed by CLI name. */
    private readonly array $commands;

    /**
     * Registers the commands that may be dispatched.
     *
     * @param list<\GustavoPeixoto\PhpQaScope\Command\Command> $commands Command instances to index by name.
     */
    public function __construct(array $commands)
    {
        $registered = [];
        foreach ($commands as $command) {
            $registered[$command->name()] = $command;
        }
        $this->commands = $registered;
    }

    /**
     * Formats usage from the registered command names in registration order.
     *
     * @return string Usage text for this registry's supported commands.
     */
    public function usage(): string
    {
        return sprintf('Usage: php-qa-scope <%s>', implode('|', array_keys($this->commands)));
    }

    /**
     * Returns the command registered for a name.
     *
     * @param string $name Command name requested by the input.
     *
     * @return \GustavoPeixoto\PhpQaScope\Command\Command Command implementation for the requested name.
     */
    public function get(string $name): Command
    {
        return $this->commands[$name] ?? throw new RuntimeException($this->usage());
    }
}
