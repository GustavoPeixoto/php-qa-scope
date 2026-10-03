<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Initializer;

/**
 * Summarizes target errors and successful native writes from initialization.
 */
final readonly class InitializerResult
{
    /**
     * Creates the aggregate result of marker insertion and synchronization.
     *
     * @param bool $hasErrors Whether any target failed during either phase.
     * @param bool $changed Whether either phase successfully modified a native file.
     */
    public function __construct(public bool $hasErrors, public bool $changed)
    {
    }
}
