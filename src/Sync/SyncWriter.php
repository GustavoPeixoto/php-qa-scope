<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Sync;

use RuntimeException;

/**
 * Replaces one divergent native target with temporary-file safety checks.
 */
final class SyncWriter
{
    /**
     * Writes one inspected target if its native file is still unchanged.
     *
     * @param string $root Project root containing the target file.
     * @param TargetInspection $inspection Validated target to update.
     */
    public function write(string $root, TargetInspection $inspection): void
    {
        if (!$inspection->changed) {
            return;
        }

        $file = $inspection->target->path;
        $path = $root . '/' . $file;
        $temp = tempnam($root, '.php-qa-scope-');
        if ($temp === false) {
            throw new RuntimeException("$file: could not create a temporary file.");
        }

        try {
            $mode = is_file($path) ? fileperms($path) : false;
            $after = $inspection->replacement();
            if (
                $mode === false
                || !chmod($temp, $mode & 0777)
                || file_put_contents($temp, $after) !== strlen($after)
            ) {
                throw new RuntimeException("$file: failed to prepare the write.");
            }

            clearstatcache(true, $path);
            if (is_link($path) || file_get_contents($path) !== $inspection->before) {
                throw new RuntimeException("$file: changed during sync; run again.");
            }

            if (!rename($temp, $path)) {
                throw new RuntimeException("$file: failed to replace configuration; run check before retrying.");
            }
        } finally {
            if (is_file($temp)) {
                unlink($temp);
            }
        }
    }
}
