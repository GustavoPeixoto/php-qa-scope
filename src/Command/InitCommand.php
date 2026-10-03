<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Command;

use GustavoPeixoto\PhpQaScope\Cli\ExitCode;
use GustavoPeixoto\PhpQaScope\Cli\Input;
use GustavoPeixoto\PhpQaScope\Console\ConsoleWriterInterface;
use GustavoPeixoto\PhpQaScope\Initializer\Initializer;

/**
 * Runs initialization and reports review guidance and the CLI exit code.
 */
final class InitCommand implements Command
{
    public const REVIEW_WARNING = "WARNING: QA configuration files were modified.\n"
        . "Review the changes and complete any required manual setup before running your QA tools.\n"
        . 'Setup instructions: https://github.com/GustavoPeixoto/php-qa-scope#managed-blocks';

    /**
     * Creates the CLI adapter for the initialization workflow.
     *
     * @param \GustavoPeixoto\PhpQaScope\Initializer\Initializer $initializer Workflow that sets up and synchronizes native files.
     */
    public function __construct(private readonly Initializer $initializer)
    {
    }

    /**
     * Returns the command name accepted by the CLI.
     *
     * @return string Initialization command name.
     */
    public function name(): string
    {
        return 'init';
    }

    /**
     * Runs initialization, emits review guidance, and maps the result to an exit code.
     *
     * @param \GustavoPeixoto\PhpQaScope\Cli\Input $input Parsed command name and project root.
     * @param \GustavoPeixoto\PhpQaScope\Console\ConsoleWriterInterface $console Destination for results, local errors, and review guidance.
     *
     * @return int Success unless preparation or synchronization encountered an error.
     */
    public function execute(Input $input, ConsoleWriterInterface $console): int
    {
        $result = $this->initializer->initialize($input->root, $console);
        if ($result->changed) {
            $console->errorLine(self::REVIEW_WARNING);
        }

        return $result->hasErrors ? ExitCode::ERROR : ExitCode::SUCCESS;
    }
}
