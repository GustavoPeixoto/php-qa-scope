<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Command;

use GustavoPeixoto\PhpQaScope\Cli\ExitCode;
use GustavoPeixoto\PhpQaScope\Cli\Input;
use GustavoPeixoto\PhpQaScope\Cli\Output;
use GustavoPeixoto\PhpQaScope\Config\ToolScope;
use GustavoPeixoto\PhpQaScope\Sync\SyncWriter;
use GustavoPeixoto\PhpQaScope\Sync\TargetInspector;
use Throwable;

/**
 * Synchronizes each managed native target independently.
 */
final class SyncCommand implements Command
{
    /**
     * Creates the command with inspection and writing collaborators.
     *
     * @param TargetInspector $inspector Loader and inspector for managed targets.
     * @param SyncWriter $writer Writer for one divergent native target.
     */
    public function __construct(
        private readonly TargetInspector $inspector,
        private readonly SyncWriter $writer,
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
     * @param Input $input Parsed command input.
     * @param Output $output Output writer for per-target statuses.
     * @return int Error when any target failed, otherwise success.
     */
    public function execute(Input $input, Output $output): int
    {
        $scopes = $this->inspector->scopes($input->root);
        $hasErrors = false;

        foreach ($scopes as $tool => $scope) {
            if (!$this->syncTarget($input->root, $tool, $scope, $output)) {
                $hasErrors = true;
            }
        }

        return $hasErrors ? ExitCode::ERROR : ExitCode::SUCCESS;
    }

    /**
     * Processes one target so its native file data is released on return.
     *
     * @param string $root Project root containing target files.
     * @param string $tool Managed tool name.
     * @param ToolScope $scope Effective scope for the tool.
     * @param Output $output Output writer for the target result.
     * @return bool True when the target matched or was updated.
     */
    private function syncTarget(string $root, string $tool, ToolScope $scope, Output $output): bool
    {
        $file = $this->inspector->target($tool)->path;

        try {
            $inspection = $this->inspector->inspect($root, $tool, $scope);
            if ($inspection->changed) {
                $this->writer->write($root, $inspection);
            }
            $output->line(($inspection->changed ? 'UPDATED ' : 'OK ') . $file);

            return true;
        } catch (Throwable $error) {
            $reason = $error->getMessage();
            if (str_starts_with($reason, "$file: ")) {
                $reason = substr($reason, strlen($file) + 2);
            }
            $output->errorLine("ERROR $file: $reason");

            return false;
        }
    }
}
