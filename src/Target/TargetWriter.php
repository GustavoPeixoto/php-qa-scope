<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Target;

use RuntimeException;

/**
 * Reads and replaces native configuration files with per-file safety checks.
 */
final class TargetWriter
{
    /**
     * Reads a regular native file while rejecting symbolic links.
     *
     * @param string $root Project root containing the file.
     * @param string $file Root-relative native configuration filename.
     *
     * @return string Observed native file bytes.
     */
    public function read(string $root, string $file): string
    {
        $path = $root . '/' . $file;
        clearstatcache(true, $path);
        if (is_link($path)) {
            throw new RuntimeException("$file: managed configuration files cannot be symbolic links.");
        }

        $before = is_file($path) ? @file_get_contents($path) : false;
        if ($before === false) {
            throw new RuntimeException("$file: could not read the configuration.");
        }

        return $before;
    }

    /**
     * Commits replacement bytes only if the inspected file is still unchanged.
     *
     * @param string $root Project root containing the file.
     * @param string $file Root-relative native configuration filename.
     * @param string $before Bytes observed before preparing replacement content.
     * @param string $after Complete replacement bytes.
     * @param string $operation Command name included in concurrent-change errors.
     */
    public function write(string $root, string $file, string $before, string $after, string $operation = 'sync'): void
    {
        $path = $root . '/' . $file;
        clearstatcache(true, $path);
        if (is_link($path)) {
            throw new RuntimeException("$file: managed configuration files cannot be symbolic links.");
        }
        if ($before === $after) {
            return;
        }

        $temp = tempnam($root, '.php-qa-scope-');
        if ($temp === false) {
            throw new RuntimeException("$file: could not create a temporary file.");
        }

        try {
            $this->prepareReplacement($path, $temp, $file, $after);
            $this->assertUnchanged($path, $file, $before, $operation);

            if (!rename($temp, $path)) {
                throw new RuntimeException("$file: failed to replace configuration; run check before retrying.");
            }
        } finally {
            if (is_file($temp)) {
                unlink($temp);
            }
        }
    }

    /**
     * Prepares replacement bytes with the native file's existing permissions.
     *
     * @param string $path Absolute native configuration path.
     * @param string $temp Temporary replacement file path.
     * @param string $file Root-relative filename included in errors.
     * @param string $after Complete replacement bytes.
     */
    private function prepareReplacement(string $path, string $temp, string $file, string $after): void
    {
        $mode = is_file($path) ? fileperms($path) : false;
        if (
            $mode === false
            || !chmod($temp, $mode & 0777)
            || file_put_contents($temp, $after) !== strlen($after)
        ) {
            throw new RuntimeException("$file: failed to prepare the write.");
        }
    }

    /**
     * Rejects changes or symbolic links immediately before native replacement.
     *
     * @param string $path Absolute native configuration path.
     * @param string $file Root-relative filename included in errors.
     * @param string $before Bytes observed during inspection.
     * @param string $operation Command name included in concurrent-change errors.
     */
    private function assertUnchanged(string $path, string $file, string $before, string $operation): void
    {
        clearstatcache(true, $path);
        if (is_link($path) || @file_get_contents($path) !== $before) {
            throw new RuntimeException("$file: changed during $operation; run again.");
        }
    }
}
