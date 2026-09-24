<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Sync;

/**
 * Holds the comparison and file data for one inspected native target.
 */
final readonly class TargetInspection
{
    /**
     * Creates a target-scoped inspection result.
     *
     * @param TargetFile $target Inspected native configuration target.
     * @param string $before Native file content observed during inspection.
     * @param LocatedBlock $block Validated managed block location.
     * @param string $expected Rendered managed block with LF line endings.
     * @param bool $changed Whether the current managed block differs.
     */
    public function __construct(
        public TargetFile $target,
        public string $before,
        public LocatedBlock $block,
        public string $expected,
        public bool $changed,
    ) {
    }

    /**
     * Builds the replacement file only when a divergent target is written.
     *
     * @return string Full target content with only managed block content replaced.
     */
    public function replacement(): string
    {
        return substr_replace(
            $this->before,
            str_replace("\n", $this->block->eol, $this->expected),
            $this->block->start,
            $this->block->length,
        );
    }
}
