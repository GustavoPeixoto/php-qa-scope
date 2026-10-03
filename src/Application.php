<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope;

use GustavoPeixoto\PhpQaScope\Block\BlockLocator;
use GustavoPeixoto\PhpQaScope\Cli\ExitCode;
use GustavoPeixoto\PhpQaScope\Cli\Input;
use GustavoPeixoto\PhpQaScope\Command\CheckCommand;
use GustavoPeixoto\PhpQaScope\Command\CommandRegistry;
use GustavoPeixoto\PhpQaScope\Command\InitCommand;
use GustavoPeixoto\PhpQaScope\Command\SyncCommand;
use GustavoPeixoto\PhpQaScope\Console\Console;
use GustavoPeixoto\PhpQaScope\Initializer\Initializer;
use GustavoPeixoto\PhpQaScope\InsertionLocator\InsertionLocatorRegistry;
use GustavoPeixoto\PhpQaScope\Renderer\RendererRegistry;
use GustavoPeixoto\PhpQaScope\Scope\ScopeCalculator;
use GustavoPeixoto\PhpQaScope\Scope\ScopeInitializer;
use GustavoPeixoto\PhpQaScope\Scope\ScopeLoader;
use GustavoPeixoto\PhpQaScope\Synchronizer\Synchronizer;
use GustavoPeixoto\PhpQaScope\Target\TargetInitializer;
use GustavoPeixoto\PhpQaScope\Target\TargetInspector;
use GustavoPeixoto\PhpQaScope\Target\TargetRegistry;
use GustavoPeixoto\PhpQaScope\Target\TargetWriter;
use Throwable;

/**
 * Runs the package command-line workflow.
 */
final class Application
{
    /**
     * Creates an application with the provided command registry.
     *
     * @param \GustavoPeixoto\PhpQaScope\Command\CommandRegistry $commands Commands available to the CLI.
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
        $loader = new ScopeLoader();
        $scopeCalculator = ScopeCalculator::default();
        $targets = TargetRegistry::default();
        $blockLocator = new BlockLocator();
        $writer = new TargetWriter();

        $inspector = new TargetInspector(
            $loader,
            $scopeCalculator,
            RendererRegistry::default(),
            $targets,
            $blockLocator,
        );

        $synchronizer = new Synchronizer(
            $inspector,
            $writer,
        );

        $initializer = new Initializer(
            $synchronizer,
            new TargetInitializer(
                InsertionLocatorRegistry::default(),
                $targets,
                $blockLocator,
                $writer,
            ),
            new ScopeInitializer(),
            $targets,
            $loader,
            $scopeCalculator,
        );

        return new self(new CommandRegistry([
            new InitCommand($initializer),
            new SyncCommand($inspector, $synchronizer),
            new CheckCommand($inspector),
        ]));
    }

    /**
     * Executes the command described by CLI arguments.
     *
     * @param list<string> $argv Command-line arguments including the executable name.
     * @param \GustavoPeixoto\PhpQaScope\Console\Console $console Console receiving command output and caught errors.
     * @param string|null $root Project root used instead of the current working directory.
     *
     * @return int Process exit code for the command.
     */
    public function run(array $argv, Console $console, ?string $root = null): int
    {
        try {
            $input = Input::fromArgv($argv, $this->commands->usage(), $root);

            return $this->commands->get($input->command)->execute($input, $console);
        } catch (Throwable $error) {
            $console->errorLine('ERROR ' . $error->getMessage());

            return ExitCode::ERROR;
        }
    }
}
