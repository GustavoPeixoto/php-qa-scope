<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Glob;

use RuntimeException;

/**
 * Compiles supported exclude pattern forms for renderers and path checks.
 */
final class PatternCompiler
{
    /**
     * Converts a supported pattern into renderer-ready fragments.
     *
     * @param string $pattern Exclude pattern from configuration.
     * @return CompiledPattern Pattern compiled for all supported renderers.
     */
    public function compile(string $pattern): CompiledPattern
    {
        PathValidator::excludePatternShape($pattern);
        $quote = static fn (string $path): string => preg_quote(PathValidator::literal($path), '~');

        if (str_starts_with($pattern, '**/*') && str_ends_with($pattern, '.php')) {
            $suffix = substr($pattern, 4);
            if ($suffix === '' || str_contains($suffix, '/')) {
                throw new RuntimeException("Unsupported pattern: '$pattern'. See README.md.");
            }

            return new CompiledPattern('(?:[^/]+/){0,}[^/]{0,}' . $quote($suffix) . '$', ['*' . $suffix]);
        }

        if (preg_match('~^(?:(.+)/)?\*\*/([^/]+)/\*\*$~D', $pattern, $parts) === 1) {
            $prefix = $parts[1] === '' ? '' : PathValidator::literal($parts[1]) . '/';
            $name = PathValidator::literal($parts[2]);

            return new CompiledPattern(
                preg_quote($prefix, '~') . '(?:[^/]+/){0,}' . $quote($name) . '/',
                [$prefix . $name . '/*', $prefix . '*/' . $name . '/*'],
            );
        }

        if (str_ends_with($pattern, '/**')) {
            $path = PathValidator::literal(substr($pattern, 0, -3));

            return new CompiledPattern($quote($path) . '/', [$path . '/*']);
        }

        if (!str_contains($pattern, '*') && str_ends_with($pattern, '.php')) {
            return new CompiledPattern($quote($pattern) . '$', [$pattern], true);
        }

        throw new RuntimeException("Unsupported pattern: '$pattern'. See README.md.");
    }

    /**
     * Checks whether a pattern matches a literal path.
     *
     * @param string $pattern Exclude pattern to evaluate.
     * @param string $path Literal path to test.
     * @return bool True when the pattern matches the path.
     */
    public function matchesPath(string $pattern, string $path): bool
    {
        $compiled = $this->compile($pattern);
        if (str_ends_with($path, '.php')) {
            return preg_match('~^' . $compiled->regex . '~D', $path) === 1;
        }

        if (!str_ends_with($path, '/')) {
            $path .= '/';
        }

        return preg_match('~^' . $compiled->regex . '~D', $path) === 1;
    }
}
