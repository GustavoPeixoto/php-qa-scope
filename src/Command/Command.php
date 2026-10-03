<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Command;

use GustavoPeixoto\PhpQaScope\Cli\Input;
use GustavoPeixoto\PhpQaScope\Console\ConsoleWriterInterface;

/**
 * Defines a command that can be dispatched by the CLI registry.
 */
interface Command
{
    /**
     * Returns the command name used for dispatch.
     *
     * @return string Command name accepted on the CLI.
     */
    public function name(): string;

    /**
     * Runs the command with parsed input and an output writer.
     *
     * @param \GustavoPeixoto\PhpQaScope\Cli\Input $input Parsed command input.
     * @param \GustavoPeixoto\PhpQaScope\Console\ConsoleWriterInterface $console Destination for user-visible messages.
     *
     * @return int Process exit code for the command.
     */
    public function execute(Input $input, ConsoleWriterInterface $console): int;
}
