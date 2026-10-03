<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Console;

/**
 * Defines line-based destinations for normal and error console messages.
 */
interface ConsoleWriterInterface
{
    /**
     * Writes one line to the normal output destination.
     *
     * @param string $line Line content without the trailing newline.
     */
    public function line(string $line): void;

    /**
     * Writes one line to the error output destination.
     *
     * @param string $line Line content without the trailing newline.
     */
    public function errorLine(string $line): void;
}
