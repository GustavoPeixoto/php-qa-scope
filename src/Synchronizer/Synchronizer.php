<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Synchronizer;

use GustavoPeixoto\PhpQaScope\Console\ConsoleWriterInterface;
use GustavoPeixoto\PhpQaScope\Scope\ToolScope;
use GustavoPeixoto\PhpQaScope\Target\TargetInspector;
use GustavoPeixoto\PhpQaScope\Target\TargetWriter;
use GustavoPeixoto\PhpQaScope\Tool;
use Throwable;

/**
 * Synchronizes selected targets independently and reports successful changes.
 */
final class Synchronizer
{
    /**
     * Creates the shared synchronization workflow.
     *
     * @param TargetInspector $inspector Validator and renderer for each target.
     * @param TargetWriter $writer Safe native file replacement collaborator.
     */
    public function __construct(
        private readonly TargetInspector $inspector,
        private readonly TargetWriter $writer,
    ) {
    }

    /**
     * Processes every selected target even after a target-local failure.
     *
     * @param string $root Project root containing native files.
     * @param array<string, ToolScope> $scopes Effective scopes indexed by tool.
     * @param ConsoleWriterInterface $console Destination for target statuses and errors.
     * @return SynchronizerResult Aggregate errors and successfully committed changes.
     */
    public function synchronize(string $root, array $scopes, ConsoleWriterInterface $console): SynchronizerResult
    {
        $hasErrors = false;
        $changed = false;

        foreach ($scopes as $toolName => $scope) {
            $tool = Tool::from($toolName);
            $file = $this->inspector->target($tool)->path;

            try {
                if ($this->syncTarget($root, $tool, $scope, $console)) {
                    $changed = true;
                }
            } catch (Throwable $error) {
                $reason = $error->getMessage();
                if (str_starts_with($reason, "$file: ")) {
                    $reason = substr($reason, strlen($file) + 2);
                }
                $console->errorLine("ERROR $file: $reason");
                $hasErrors = true;
            }
        }

        return new SynchronizerResult($hasErrors, $changed);
    }

    /**
     * Releases one target's file data before the next target is inspected.
     *
     * @param string $root Project root containing native files.
     * @param Tool $tool Managed tool name.
     * @param ToolScope $scope Effective scope for this tool.
     * @param ConsoleWriterInterface $console Destination for the target status.
     * @return bool Whether the target was successfully updated.
     */
    private function syncTarget(string $root, Tool $tool, ToolScope $scope, ConsoleWriterInterface $console): bool
    {
        $inspection = $this->inspector->inspect($root, $tool, $scope);
        if ($inspection->changed) {
            $this->writer->write(
                $root,
                $inspection->target->path,
                $inspection->before,
                $inspection->replacement(),
            );
        }
        $console->line(($inspection->changed ? 'UPDATED ' : 'OK ') . $inspection->target->path);

        return $inspection->changed;
    }
}
