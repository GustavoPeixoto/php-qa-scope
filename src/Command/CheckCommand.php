<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Command;

use GustavoPeixoto\PhpQaScope\Cli\ExitCode;
use GustavoPeixoto\PhpQaScope\Cli\Input;
use GustavoPeixoto\PhpQaScope\Cli\Output;
use GustavoPeixoto\PhpQaScope\Config\ToolScope;
use GustavoPeixoto\PhpQaScope\Sync\TargetInspector;
use Throwable;

/**
 * Reports the synchronization status of each managed native target.
 */
final class CheckCommand implements Command
{
    /**
     * Creates the command with its shared target inspector.
     *
     * @param TargetInspector $inspector Loader and inspector for managed targets.
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
     * @param Input $input Parsed command input.
     * @param Output $output Output writer for statuses and guidance.
     * @return int Exit code for errors, drift, or success.
     */
    public function execute(Input $input, Output $output): int
    {
        $scopes = $this->inspector->scopes($input->root);
        $hasErrors = false;
        $hasDrift = false;

        foreach ($scopes as $tool => $scope) {
            $result = $this->checkTarget($input->root, $tool, $scope, $output);
            $hasErrors = $hasErrors || $result === ExitCode::ERROR;
            $hasDrift = $hasDrift || $result === ExitCode::DRIFT;
        }

        if ($hasDrift) {
            $output->line('Run vendor/bin/php-qa-scope sync to synchronize the blocks.');
        }

        return $hasErrors ? ExitCode::ERROR : ($hasDrift ? ExitCode::DRIFT : ExitCode::SUCCESS);
    }

    /**
     * Inspects one target and releases its file data before the next target.
     *
     * @param string $root Project root containing target files.
     * @param string $tool Managed tool name.
     * @param ToolScope $scope Effective scope for the tool.
     * @param Output $output Output writer for the target result.
     * @return int Target result as a command exit code.
     */
    private function checkTarget(string $root, string $tool, ToolScope $scope, Output $output): int
    {
        $file = $this->inspector->target($tool)->path;

        try {
            $changed = $this->inspector->inspect($root, $tool, $scope)->changed;
            $output->line(($changed ? 'OUT-OF-SYNC ' : 'OK ') . $file);

            return $changed ? ExitCode::DRIFT : ExitCode::SUCCESS;
        } catch (Throwable $error) {
            $reason = $error->getMessage();
            if (str_starts_with($reason, "$file: ")) {
                $reason = substr($reason, strlen($file) + 2);
            }
            $output->errorLine("ERROR $file: $reason");

            return ExitCode::ERROR;
        }
    }
}
