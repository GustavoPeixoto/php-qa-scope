<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Cli;

/**
 * Buffers command output while optionally mirroring it to streams.
 */
final class Output
{
    private string $stdout = '';
    private string $stderr = '';

    /**
     * Creates an output buffer with optional stream mirrors.
     *
     * @param resource|null $out Stream for normal output, or null to buffer only.
     * @param resource|null $err Stream for error output, or null to buffer only.
     */
    public function __construct(
        private $out = null,
        private $err = null,
    ) {
    }

    /**
     * Writes one line to standard output.
     *
     * @param string $line Line content without the trailing newline.
     */
    public function line(string $line): void
    {
        $this->write($line . "\n");
    }

    /**
     * Writes one line to standard error.
     *
     * @param string $line Line content without the trailing newline.
     */
    public function errorLine(string $line): void
    {
        $this->writeError($line . "\n");
    }

    /**
     * Returns all buffered standard output.
     *
     * @return string Output accumulated through line writes.
     */
    public function stdout(): string
    {
        return $this->stdout;
    }

    /**
     * Returns all buffered standard error.
     *
     * @return string Error output accumulated through error line writes.
     */
    public function stderr(): string
    {
        return $this->stderr;
    }

    /**
     * Appends text to the standard output buffer and stream.
     *
     * @param string $text Text to append exactly as provided.
     */
    private function write(string $text): void
    {
        $this->stdout .= $text;
        if (is_resource($this->out)) {
            fwrite($this->out, $text);
        }
    }

    /**
     * Appends text to the standard error buffer and stream.
     *
     * @param string $text Text to append exactly as provided.
     */
    private function writeError(string $text): void
    {
        $this->stderr .= $text;
        if (is_resource($this->err)) {
            fwrite($this->err, $text);
        }
    }
}
