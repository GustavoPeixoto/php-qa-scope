<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Command;

use GustavoPeixoto\PhpQaScope\Cli\ExitCode;
use GustavoPeixoto\PhpQaScope\Cli\Input;
use GustavoPeixoto\PhpQaScope\Console\ConsoleWriterInterface;
use GustavoPeixoto\PhpQaScope\Scope\ToolScope;
use GustavoPeixoto\PhpQaScope\Target\TargetInspector;
use GustavoPeixoto\PhpQaScope\Tool;
use Throwable;

/**
 * Reports the synchronization status of each managed native target.
 */
final class CheckCommand implements Command
{
    /**
     * Creates the command with its shared target inspector.
     *
     * @param \GustavoPeixoto\PhpQaScope\Target\TargetInspector $inspector Loader and inspector for managed targets.
     */
    public function __construct(private readonly TargetInspector $inspector)
    {
    }

    /**
     * Returns the command name used on the CLI.
     *
     * @return string Command name accepted by the registry.
     */
    public function name(): string
    {
        return 'check';
    }

    /**
     * Inspects all managed targets and aggregates their results.
     *
     * @param \GustavoPeixoto\PhpQaScope\Cli\Input $input Parsed command input.
     * @param \GustavoPeixoto\PhpQaScope\Console\ConsoleWriterInterface $console Destination for statuses and guidance.
     *
     * @return int Exit code for errors, drift, or success.
     */
    public function execute(Input $input, ConsoleWriterInterface $console): int
    {
        $scopes = $this->inspector->scopes($input->root);
        $hasErrors = false;
        $hasDrift = false;

        foreach ($scopes as $tool => $scope) {
            $result = $this->checkTarget($input->root, Tool::from($tool), $scope, $console);
            $hasErrors = $hasErrors || $result === ExitCode::ERROR;
            $hasDrift = $hasDrift || $result === ExitCode::DRIFT;
        }

        if ($hasDrift) {
            $console->line('Run vendor/bin/php-qa-scope sync to synchronize the blocks.');
        }

        return $hasErrors ? ExitCode::ERROR : ($hasDrift ? ExitCode::DRIFT : ExitCode::SUCCESS);
    }

    /**
     * Inspects one target and releases its file data before the next target.
     *
     * @param string $root Project root containing target files.
     * @param \GustavoPeixoto\PhpQaScope\Tool $tool Managed tool name.
     * @param \GustavoPeixoto\PhpQaScope\Scope\ToolScope $scope Effective scope for the tool.
     * @param \GustavoPeixoto\PhpQaScope\Console\ConsoleWriterInterface $console Destination for the target result.
     *
     * @return int Target result as a command exit code.
     */
    private function checkTarget(string $root, Tool $tool, ToolScope $scope, ConsoleWriterInterface $console): int
    {
        $file = $this->inspector->target($tool)->path;

        try {
            $changed = $this->inspector->inspect($root, $tool, $scope)->changed;
            $console->line(($changed ? 'OUT-OF-SYNC ' : 'OK ') . $file);

            return $changed ? ExitCode::DRIFT : ExitCode::SUCCESS;
        } catch (Throwable $error) {
            $reason = $error->getMessage();
            if (str_starts_with($reason, "$file: ")) {
                $reason = substr($reason, strlen($file) + 2);
            }
            $console->errorLine("ERROR $file: $reason");

            return ExitCode::ERROR;
        }
    }
}
