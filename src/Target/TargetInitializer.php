<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Target;

use GustavoPeixoto\PhpQaScope\Block\BlockLocator;
use GustavoPeixoto\PhpQaScope\InsertionLocator\InsertionLocatorRegistry;
use GustavoPeixoto\PhpQaScope\Tool;
use RuntimeException;

/**
 * Persists empty marker pairs or validates an existing pair without rendering.
 */
final class TargetInitializer
{
    /**
     * Creates the marker insertion workflow with an injected strategy registry.
     *
     * @param \GustavoPeixoto\PhpQaScope\InsertionLocator\InsertionLocatorRegistry $locators Insertion strategies indexed by tool.
     * @param \GustavoPeixoto\PhpQaScope\Target\TargetRegistry $targets Native filenames, syntax, and indentation.
     * @param \GustavoPeixoto\PhpQaScope\Block\BlockLocator $blockLocator Strict validator for existing and inserted pairs.
     * @param \GustavoPeixoto\PhpQaScope\Target\TargetWriter $writer Safe native reads and replacements.
     */
    public function __construct(
        private readonly InsertionLocatorRegistry $locators,
        private readonly TargetRegistry $targets,
        private readonly BlockLocator $blockLocator,
        private readonly TargetWriter $writer,
    ) {
    }

    /**
     * Builds a standalone marker preparer for the supported native tools.
     *
     * @return self Service configured with built-in collaborators.
     */
    public static function default(): self
    {
        return new self(
            InsertionLocatorRegistry::default(),
            TargetRegistry::default(),
            new BlockLocator(),
            new TargetWriter(),
        );
    }

    /**
     * Adds an absent pair and leaves every pre-existing valid pair unchanged.
     *
     * @param string $root Project root containing native configuration files.
     * @param \GustavoPeixoto\PhpQaScope\Tool $tool Managed tool whose markers are being prepared.
     *
     * @return bool Whether an empty pair was successfully written.
     */
    public function insert(string $root, Tool $tool): bool
    {
        $target = $this->targets->get($tool);
        $before = $this->writer->read($root, $target->path);
        if (str_contains($before, 'php-qa-scope:start') || str_contains($before, 'php-qa-scope:end')) {
            $this->blockLocator->locate($before, $target);

            return false;
        }

        try {
            $locator = $this->locators->get($tool);
            $offset = $locator->locate($before);
        } catch (RuntimeException $error) {
            throw new RuntimeException(
                "$target->path: " . $error->getMessage()
                . ' Place the markers manually; see '
                . 'https://github.com/GustavoPeixoto/php-qa-scope#managed-blocks',
                0,
                $error,
            );
        }

        preg_match('/\r?\n/', $before, $newlines);
        $eol = $newlines[0] ?? "\n";
        $separator = $offset > 0 && $before[$offset - 1] !== "\n" ? $eol : '';
        $pair = $separator
            . $target->indent
            . sprintf($target->marker, 'start')
            . $eol
            . $target->indent
            . sprintf($target->marker, 'end')
            . $eol
        ;
        $after = substr_replace($before, $pair, $offset, 0);
        $this->blockLocator->locate($after, $target);
        $this->writer->write($root, $target->path, $before, $after, 'init');

        return true;
    }
}
