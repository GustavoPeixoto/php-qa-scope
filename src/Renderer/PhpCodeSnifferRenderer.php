<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Renderer;

use GustavoPeixoto\PhpQaScope\Config\ToolScope;
use GustavoPeixoto\PhpQaScope\Glob\PatternCompiler;

/**
 * Renders managed PHPCS scope XML entries.
 */
final class PhpCodeSnifferRenderer implements Renderer
{
    /**
     * Creates the renderer with the pattern compiler used for excludes.
     *
     * @param PatternCompiler $patterns Compiler for supported exclude patterns.
     */
    public function __construct(private readonly PatternCompiler $patterns = new PatternCompiler())
    {
    }

    /**
     * Renders the managed PHPCS block for a tool scope.
     *
     * @param ToolScope $scope Scope to render into PHPCS XML.
     * @return string XML fragment for the managed scope block.
     */
    public function render(ToolScope $scope): string
    {
        $xml = static fn (string $text): string => htmlspecialchars($text, ENT_QUOTES | ENT_XML1, 'UTF-8');
        $lines = ['    <file>.</file>', '    <arg name="extensions" value="php"/>'];
        $patterns = [
            '(?-i)^(?!' . $this->includeRegex($scope->include) . ').+',
            '(?-i)^(?!' . $this->includeRegex($scope->include, true) . ').+/*',
            ...$this->hiddenDirectoryPatterns($scope->include),
        ];

        foreach ($scope->exclude as $pattern) {
            $regex = $this->patterns->compile($pattern)->regex;
            $patterns[] = '(?-i)^' . (str_ends_with($pattern, '/**') ? substr($regex, 0, -1) . '/*' : $regex);
        }

        foreach ($scope->include as $path) {
            if (!str_ends_with($path, '.php') || !$this->hasHiddenSegment($path)) {
                continue;
            }

            foreach ($scope->exclude as $pattern) {
                if ($this->patterns->matchesPath($pattern, $path)) {
                    continue 2;
                }
            }

            $lines[] = '    <file>' . $xml($path) . '</file>';
        }

        foreach ($patterns as $pattern) {
            $lines[] = '    <exclude-pattern type="relative">' . $xml($pattern) . '</exclude-pattern>';
        }

        return implode("\n", $lines) . "\n";
    }

    /**
     * Builds a regular expression matching included files or directories.
     *
     * @param list<string> $paths Include paths to convert.
     * @param bool $directories Whether parent directories should be included.
     * @return string Regular expression fragment for include matching.
     */
    private function includeRegex(array $paths, bool $directories = false): string
    {
        $alternatives = [];

        foreach ($paths as $path) {
            $isFile = str_ends_with($path, '.php');
            if (!$directories || !$isFile) {
                $alternatives[] = preg_quote($path, '~') . ($isFile ? '$' : '(?:/|$)');
            }

            if ($directories) {
                $parent = dirname($path);
                while ($parent !== '.') {
                    $alternatives[] = preg_quote($parent, '~') . '$';
                    $parent = dirname($parent);
                }
            }
        }

        return $alternatives === [] ? '(?!)' : '(?:' . implode('|', array_unique($alternatives)) . ')';
    }

    /**
     * Builds PHPCS directory exclusions while keeping explicitly included hidden roots traversable.
     *
     * @param list<string> $includes Paths explicitly included for PHPCS.
     * @return list<string> Exclusion patterns for hidden directories.
     */
    private function hiddenDirectoryPatterns(array $includes): array
    {
        $protected = [];
        foreach ($includes as $include) {
            if (str_ends_with($include, '.php')) {
                continue;
            }

            $segments = explode('/', $include);
            $prefix = '';
            foreach ($segments as $segment) {
                $prefix = $prefix === '' ? $segment : $prefix . '/' . $segment;
                if (str_starts_with($segment, '.')) {
                    $protected[] = $prefix;
                }
            }
        }

        $protected = array_values(array_unique($protected));
        $patterns = [];
        foreach (['', ...$protected] as $root) {
            $exceptions = [];
            foreach ($protected as $path) {
                if ($root === '') {
                    $exceptions[] = preg_quote($path, '~');
                } elseif (str_starts_with($path, $root . '/')) {
                    $exceptions[] = preg_quote(substr($path, strlen($root) + 1), '~');
                }
            }

            $prefix = $root === '' ? '' : preg_quote($root, '~') . '/';
            $except = $exceptions === [] ? '' : '(?!(?:' . implode('|', $exceptions) . ')(?:/|$))';
            $patterns[] = '(?-i)^' . $prefix . $except . '(?:[^/]+/){0,}\\.[^/]+/*';
        }

        return $patterns;
    }

    /**
     * Checks whether a path contains a segment that directory traversal hides.
     *
     * @param string $path Project-relative PHP file path.
     * @return bool True when a path segment begins with a dot.
     */
    private function hasHiddenSegment(string $path): bool
    {
        foreach (explode('/', $path) as $segment) {
            if (str_starts_with($segment, '.')) {
                return true;
            }
        }

        return false;
    }
}
