<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Glob;

use RuntimeException;

/**
 * Validates path and pattern shapes accepted by php-qa-scope.
 */
final class PathValidator
{
    /**
     * Validates a literal repository-relative path.
     *
     * @param string $path Path to validate.
     * @return string The validated path.
     */
    public static function literal(string $path): string
    {
        if (!preg_match('~^[a-zA-Z0-9_. -]+(?:/[a-zA-Z0-9_. -]+)*$~D', $path)) {
            throw new RuntimeException("Unsupported path: '$path'. Use relative paths with /.");
        }

        foreach (explode('/', $path) as $segment) {
            if (
                $segment === ''
                || $segment === '.'
                || $segment === '..'
                || trim($segment) !== $segment
                || str_ends_with($segment, '.')
            ) {
                throw new RuntimeException("Invalid path segment in '$path'.");
            }
        }

        return $path;
    }

    /**
     * Validates the broad shape of an exclude pattern before compilation.
     *
     * @param string $pattern Exclude pattern to validate.
     */
    public static function excludePatternShape(string $pattern): void
    {
        if ($pattern === '' || str_starts_with($pattern, '/') || str_contains($pattern, '\\')) {
            throw new RuntimeException("Unsupported pattern: '$pattern'. See README.md.");
        }
    }
}
