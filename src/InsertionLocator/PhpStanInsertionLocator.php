<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\InsertionLocator;

use RuntimeException;

/**
 * Finds an unambiguous conventional top-level PHPStan parameters block.
 */
final class PhpStanInsertionLocator implements InsertionLocator
{
    /**
     * Locates the start of a parameters body with compatible indentation.
     *
     * @param string $contents Original NEON configuration bytes.
     *
     * @return int Offset immediately after the parameters header line.
     */
    public function locate(string $contents): int
    {
        $count = preg_match_all('~^(?:parameters|[\'\"]parameters[\'\"])[ \t]*:~m', $contents);
        if (
            $count !== 1
            || preg_match(
                '~^parameters:[ \t]*(?:#[^\r\n]*)?(?:\r?\n|$)~m',
                $contents,
                $match,
                PREG_OFFSET_CAPTURE,
            ) !== 1
        ) {
            throw new RuntimeException('could not recognize one top-level block-form parameters section.');
        }

        $offset = $match[0][1] + strlen($match[0][0]);
        $lines = preg_split('/\r?\n/', substr($contents, $offset));
        foreach ($lines === false ? [] : $lines as $line) {
            $trimmed = trim($line);
            if ($trimmed === '' || str_starts_with($trimmed, '#')) {
                continue;
            }
            if ($line[0] !== ' ' && $line[0] !== "\t") {
                break;
            }
            if (preg_match('/^ {4}\S/', $line) !== 1) {
                throw new RuntimeException('parameters indentation requires manual marker placement.');
            }

            break;
        }

        return $offset;
    }
}
