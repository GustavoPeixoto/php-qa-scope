<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\InsertionLocator;

/**
 * Locates a conventional insertion boundary without rewriting native content.
 */
interface InsertionLocator
{
    /**
     * Finds the byte offset where an empty managed pair can be inserted.
     *
     * @param string $contents Original native configuration bytes.
     * @return int Safe insertion offset within the original file.
     */
    public function locate(string $contents): int;
}
