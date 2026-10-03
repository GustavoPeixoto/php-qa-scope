<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Command;

use GustavoPeixoto\PhpQaScope\Cli\ExitCode;
use GustavoPeixoto\PhpQaScope\Cli\Input;
use GustavoPeixoto\PhpQaScope\Console\ConsoleWriterInterface;
use GustavoPeixoto\PhpQaScope\Synchronizer\Synchronizer;
use GustavoPeixoto\PhpQaScope\Target\TargetInspector;

/**
 * Synchronizes each managed native target independently.
 */
final class SyncCommand implements Command
{
    /**
     * Creates the command with scope loading and shared synchronization.
     *
     * @param \GustavoPeixoto\PhpQaScope\Target\TargetInspector $inspector Loader and inspector for managed targets.
     * @param \GustavoPeixoto\PhpQaScope\Synchronizer\Synchronizer $synchronizer Workflow for synchronizing managed targets.
     */
    public function __construct(
        private readonly TargetInspector $inspector,
        private readonly Synchronizer $synchronizer,
    ) {
    }

    /**
     * Returns the command name used on the CLI.
     *
     * @return string Command name accepted by the registry.
     */
    public function name(): string
    {
        return 'sync';
    }

    /**
     * Updates each valid divergent target and aggregates any local errors.
     *
     * @param \GustavoPeixoto\PhpQaScope\Cli\Input $input Parsed command input.
     * @param \GustavoPeixoto\PhpQaScope\Console\ConsoleWriterInterface $console Destination for per-target statuses.
     *
     * @return int Error when any target failed, otherwise success.
     */
    public function execute(Input $input, ConsoleWriterInterface $console): int
    {
        $result = $this->synchronizer->synchronize(
            $input->root,
            $this->inspector->scopes($input->root),
            $console,
        );

        return $result->hasErrors ? ExitCode::ERROR : ExitCode::SUCCESS;
    }
}
