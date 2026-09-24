<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Sync;

use RuntimeException;

/**
 * Finds managed php-qa-scope marker blocks in target files.
 */
final class ManagedBlock
{
    /**
     * Locates the content between managed start and end markers.
     *
     * @param string $text Full target file content.
     * @param TargetFile $target Target file marker definition.
     * @return LocatedBlock Located block content and replacement metadata.
     */
    public function locate(string $text, TargetFile $target): LocatedBlock
    {
        foreach (['start', 'end'] as $edge) {
            if (substr_count($text, "php-qa-scope:$edge") !== 1) {
                throw new RuntimeException("$target->path: expected exactly one php-qa-scope:$edge marker.");
            }
        }

        $start = $target->indent . sprintf($target->marker, 'start');
        $end = $target->indent . sprintf($target->marker, 'end');
        $expression = '~^' . preg_quote($start, '~') . '(\r?\n)(.*?)^' . preg_quote($end, '~') . '(?=\r?$)~ms';

        if (preg_match($expression, $text, $match, PREG_OFFSET_CAPTURE) !== 1) {
            throw new RuntimeException("$target->path: reversed, incomplete, or invalidly indented markers.");
        }

        return new LocatedBlock($match[2][1], strlen($match[2][0]), $match[1][0], $match[2][0]);
    }
}
