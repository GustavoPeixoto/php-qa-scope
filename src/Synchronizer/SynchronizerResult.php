<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Synchronizer;

/**
 * Summarizes target errors and successful writes from synchronization.
 */
final readonly class SynchronizerResult
{
    /**
     * Creates the aggregate result of a synchronization run.
     *
     * @param bool $hasErrors Whether any managed target failed.
     * @param bool $changed Whether any native file was successfully replaced.
     */
    public function __construct(public bool $hasErrors, public bool $changed)
    {
    }
}
