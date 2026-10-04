<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Renderer;

use GustavoPeixoto\PhpQaScope\Glob\PatternCompiler;
use GustavoPeixoto\PhpQaScope\Scope\ToolScope;

/**
 * Renders managed PHPCS scope XML entries.
 */
final class PhpCodeSnifferRenderer implements Renderer
{
    /**
     * Creates the renderer with the pattern compiler used for excludes.
     *
     * @param \GustavoPeixoto\PhpQaScope\Glob\PatternCompiler $patternCompiler Compiler for supported exclude patterns.
     */
    public function __construct(private readonly PatternCompiler $patternCompiler)
    {
    }

    /**
     * Builds a standalone service with the supported pattern compiler.
     *
     * @return self Service configured with built-in collaborators.
     */
    public static function default(): self
    {
        return new self(new PatternCompiler());
    }

    /**
     * Renders the managed PHPCS block for a tool scope.
     *
     * @param \GustavoPeixoto\PhpQaScope\Scope\ToolScope $scope Scope to render into PHPCS XML.
     *
     * @return string XML fragment for the managed scope block.
     */
    public function render(ToolScope $scope): string
    {
        $xml = static fn (string $text): string => htmlspecialchars($text, ENT_QUOTES | ENT_XML1, 'UTF-8');
        $lines = [
            '    <file>.</file>',
            '    <arg name="extensions" value="php"/>',
        ];
        $patternCompiler = [
            '(?-i)^(?!' . $this->includeRegex($scope->include) . ').+',
            '(?-i)^(?!' . $this->traversalRegex($scope->include) . ').+/*',
            ...$this->hiddenDirectoryPatterns($scope->include),
        ];

        foreach ($scope->exclude as $pattern) {
            $regex = $this->patternCompiler->compile($pattern)->regex;
            $patternCompiler[] = '(?-i)^' . (str_ends_with($pattern, '/**') ? substr($regex, 0, -1) . '/*' : $regex);
        }

        foreach ($scope->include as $path) {
            if (!str_ends_with($path, '.php') || !$this->hasHiddenSegment($path)) {
                continue;
            }

            foreach ($scope->exclude as $pattern) {
                if ($this->patternCompiler->matchesPath($pattern, $path)) {
                    continue 2;
                }
            }

            $lines[] = '    <file>' . $xml($path) . '</file>';
        }

        foreach ($patternCompiler as $pattern) {
            $lines[] = '    <exclude-pattern type="relative">' . $xml($pattern) . '</exclude-pattern>';
        }

        return implode("\n", $lines) . "\n";
    }

    /**
     * Builds a regex matching explicitly included paths and directory descendants.
     *
     * @param list<string> $paths Include paths to convert.
     *
     * @return string Regular expression fragment for include matching.
     */
    private function includeRegex(array $paths): string
    {
        $alternatives = [];

        foreach ($paths as $path) {
            $suffix = str_ends_with($path, '.php') ? '$' : '(?:/|$)';
            $alternatives[] = preg_quote($path, '~') . $suffix;
        }

        return $this->alternativesRegex($alternatives);
    }

    /**
     * Builds a regex matching directories required to reach included paths.
     *
     * @param list<string> $paths Include paths to reach.
     *
     * @return string Regular expression fragment for directory traversal.
     */
    private function traversalRegex(array $paths): string
    {
        $alternatives = [];

        foreach ($paths as $path) {
            if (!str_ends_with($path, '.php')) {
                $alternatives[] = preg_quote($path, '~') . '(?:/|$)';
            }

            $parent = dirname($path);
            while ($parent !== '.') {
                $alternatives[] = preg_quote($parent, '~') . '$';
                $parent = dirname($parent);
            }
        }

        return $this->alternativesRegex($alternatives);
    }

    /**
     * Combines regular expression alternatives, removing duplicates.
     *
     * @param list<string> $alternatives Regular expression fragments to combine.
     *
     * @return string Combined fragment, or a fragment that never matches.
     */
    private function alternativesRegex(array $alternatives): string
    {
        return $alternatives === [] ? '(?!)' : '(?:' . implode('|', array_unique($alternatives)) . ')';
    }

    /**
     * Builds PHPCS directory exclusions while keeping explicitly included hidden roots traversable.
     *
     * @param list<string> $includes Paths explicitly included for PHPCS.
     *
     * @return list<string> Exclusion patterns for hidden directories.
     */
    private function hiddenDirectoryPatterns(array $includes): array
    {
        $protected = $this->protectedHiddenRoots($includes);
        $patterns = [];
        foreach (['', ...$protected] as $root) {
            $patterns[] = $this->hiddenDirectoryPattern($root, $protected);
        }

        return $patterns;
    }

    /**
     * Collects hidden directory roots preserved by explicit directory includes.
     *
     * @param list<string> $includes Paths explicitly included for PHPCS.
     *
     * @return list<string> Unique hidden directory roots in include order.
     */
    private function protectedHiddenRoots(array $includes): array
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
                if (!str_starts_with($segment, '.')) {
                    continue;
                }

                $protected[] = $prefix;
            }
        }

        return array_values(array_unique($protected));
    }

    /**
     * Builds a hidden directory exclusion while preserving protected descendants.
     *
     * @param string $root Root to traverse, or an empty string for the project root.
     * @param list<string> $protected Explicitly included hidden directory roots.
     *
     * @return string PHPCS exclusion pattern for hidden directories below the root.
     */
    private function hiddenDirectoryPattern(string $root, array $protected): string
    {
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

        return '(?-i)^' . $prefix . $except . '(?:[^/]+/){0,}\\.[^/]+/*';
    }

    /**
     * Checks whether a path contains a segment that directory traversal hides.
     *
     * @param string $path Project-relative PHP file path.
     *
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
