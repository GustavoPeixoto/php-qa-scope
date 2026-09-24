<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Command;

use GustavoPeixoto\PhpQaScope\Cli\Input;
use GustavoPeixoto\PhpQaScope\Cli\Output;

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
     * @param Input $input Parsed command input.
     * @param Output $output Output writer for user-visible messages.
     * @return int Process exit code for the command.
     */
    public function execute(Input $input, Output $output): int;
}
