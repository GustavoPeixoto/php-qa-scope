<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope;

use GustavoPeixoto\PhpQaScope\Cli\ExitCode;
use GustavoPeixoto\PhpQaScope\Cli\Input;
use GustavoPeixoto\PhpQaScope\Cli\Output;
use GustavoPeixoto\PhpQaScope\Command\CheckCommand;
use GustavoPeixoto\PhpQaScope\Command\CommandRegistry;
use GustavoPeixoto\PhpQaScope\Command\InitCommand;
use GustavoPeixoto\PhpQaScope\Command\SyncCommand;
use GustavoPeixoto\PhpQaScope\Initializer\Initializer;
use GustavoPeixoto\PhpQaScope\Target\TargetInitializer;
use GustavoPeixoto\PhpQaScope\InsertionLocator\InsertionLocatorRegistry;
use GustavoPeixoto\PhpQaScope\Target\TargetWriter;
use GustavoPeixoto\PhpQaScope\Synchronizer\Synchronizer;
use GustavoPeixoto\PhpQaScope\Target\TargetInspector;
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
        $synchronizer = new Synchronizer($inspector, new TargetWriter());

        return new self(new CommandRegistry([
            new CheckCommand($inspector),
            new SyncCommand($inspector, $synchronizer),
            new InitCommand(new Initializer($synchronizer, new TargetInitializer(InsertionLocatorRegistry::default()))),
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
