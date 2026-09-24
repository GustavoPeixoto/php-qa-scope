<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Sync;

/**
 * Describes the managed block located inside a target file.
 */
final readonly class LocatedBlock
{
    /**
     * Creates a located managed block value.
     *
     * @param int $start Byte offset where managed content starts.
     * @param int $length Byte length of the managed content.
     * @param string $eol Line ending used by the target block.
     * @param string $content Current managed block content.
     */
    public function __construct(
        public int $start,
        public int $length,
        public string $eol,
        public string $content,
    ) {
    }
}
