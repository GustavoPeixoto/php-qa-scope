<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Console;

/**
 * Provides console access through an explicitly supplied writer.
 */
final class Console implements ConsoleWriterInterface
{
    /**
     * Creates a console that delegates output to the supplied writer.
     *
     * @param ConsoleWriterInterface $writer Destination for normal and error messages.
     */
    public function __construct(private readonly ConsoleWriterInterface $writer)
    {
    }

    /**
     * Delegates a normal output line to the writer.
     *
     * @param string $line Line content without the trailing newline.
     */
    public function line(string $line): void
    {
        $this->writer->line($line);
    }

    /**
     * Delegates an error output line to the writer.
     *
     * @param string $line Line content without the trailing newline.
     */
    public function errorLine(string $line): void
    {
        $this->writer->errorLine($line);
    }
}
