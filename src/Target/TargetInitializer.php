<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Target;

use GustavoPeixoto\PhpQaScope\InsertionLocator\InsertionLocatorRegistry;
use GustavoPeixoto\PhpQaScope\Block\ManagedBlock;
use GustavoPeixoto\PhpQaScope\Target\TargetWriter;
use GustavoPeixoto\PhpQaScope\Target\TargetRegistry;
use RuntimeException;

/**
 * Persists empty marker pairs or validates an existing pair without rendering.
 */
final class TargetInitializer
{
    /**
     * Creates the marker insertion workflow with an injected strategy registry.
     *
     * @param InsertionLocatorRegistry $locators Insertion strategies indexed by tool.
     * @param TargetRegistry $targets Native filenames, syntax, and indentation.
     * @param ManagedBlock $blocks Strict validator for existing and inserted pairs.
     * @param TargetWriter $files Safe native reads and replacements.
     */
    public function __construct(
        private readonly InsertionLocatorRegistry $locators,
        private readonly TargetRegistry $targets = new TargetRegistry(),
        private readonly ManagedBlock $blocks = new ManagedBlock(),
        private readonly TargetWriter $files = new TargetWriter(),
    ) {
    }

    /**
     * Adds an absent pair and leaves every pre-existing valid pair unchanged.
     *
     * @param string $root Project root containing native configuration files.
     * @param string $tool Managed tool whose markers are being prepared.
     * @return bool Whether an empty pair was successfully written.
     */
    public function insert(string $root, string $tool): bool
    {
        $target = $this->targets->get($tool);
        $before = $this->files->read($root, $target->path);
        if (str_contains($before, 'php-qa-scope:start') || str_contains($before, 'php-qa-scope:end')) {
            $this->blocks->locate($before, $target);

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
        $this->blocks->locate($after, $target);
        $this->files->write($root, $target->path, $before, $after, 'init');

        return true;
    }
}
