<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope;

use GustavoPeixoto\PhpQaScope\Cli\ExitCode;
use GustavoPeixoto\PhpQaScope\Cli\Input;
use GustavoPeixoto\PhpQaScope\Cli\Output;
use GustavoPeixoto\PhpQaScope\Command\CheckCommand;
use GustavoPeixoto\PhpQaScope\Command\CommandRegistry;
use GustavoPeixoto\PhpQaScope\Command\SyncCommand;
use GustavoPeixoto\PhpQaScope\Sync\SyncWriter;
use GustavoPeixoto\PhpQaScope\Sync\TargetInspector;
use Throwable;

/**
 * Runs the package command-line workflow.
 */
final class Application
{
    /**
     * Creates an application with the provided command registry.
     *
     * @param CommandRegistry $commands Commands available to the CLI.
     */
    public function __construct(private readonly CommandRegistry $commands)
    {
    }

    /**
     * Builds the default application with the built-in commands.
     *
     * @return self Application configured for normal package usage.
     */
    public static function default(): self
    {
        $inspector = TargetInspector::default();

        return new self(new CommandRegistry([
            new CheckCommand($inspector),
            new SyncCommand($inspector, new SyncWriter()),
        ]));
    }

    /**
     * Executes the command described by CLI arguments.
     *
     * @param list<string> $argv Command-line arguments including the executable name.
     * @param string|null $root Project root used instead of the current working directory.
     * @param resource|null $stdout Stream receiving normal output, or null to buffer only.
     * @param resource|null $stderr Stream receiving error output, or null to buffer only.
     * @return int Process exit code for the command.
     */
    public function run(array $argv, ?string $root = null, $stdout = null, $stderr = null): int
    {
        $output = new Output($stdout, $stderr);

        try {
            $input = Input::fromArgv($argv, $root);

            return $this->commands->get($input->command)->execute($input, $output);
        } catch (Throwable $error) {
            $output->errorLine('ERROR ' . $error->getMessage());

            return ExitCode::ERROR;
        }
    }
}
