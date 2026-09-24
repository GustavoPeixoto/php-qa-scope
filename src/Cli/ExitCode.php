<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Cli;

/**
 * Defines process exit codes emitted by the CLI.
 */
final class ExitCode
{
    public const SUCCESS = 0;
    public const DRIFT = 1;
    public const ERROR = 2;
}
