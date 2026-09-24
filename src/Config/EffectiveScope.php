<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Config;

use GustavoPeixoto\PhpQaScope\Glob\PathValidator;
use GustavoPeixoto\PhpQaScope\Glob\PatternCompiler;
use RuntimeException;

/**
 * Calculates per-tool scopes after applying global and local configuration.
 */
final class EffectiveScope
{
    /**
     * Creates the calculator with the pattern compiler used for exclusions.
     *
     * @param PatternCompiler $patterns Compiler for supported exclude patterns.
     */
    public function __construct(private readonly PatternCompiler $patterns = new PatternCompiler())
    {
    }

    /**
     * Resolves effective include and exclude lists for every managed tool.
     *
     * @param ScopeConfig $config Loaded package scope configuration.
     * @return array<string, ToolScope> Effective scopes indexed by tool name.
     */
    public function calculate(ScopeConfig $config): array
    {
        $result = [];

        foreach ($config->managedTools() as $tool) {
            $local = $config->tool($tool);
            $include = $this->stringSet([...$config->include, ...$local->include]);
            $exclude = $this->stringSet([...$config->exclude, ...$local->exclude]);

            foreach ($include as $path) {
                PathValidator::literal($path);
            }

            foreach ($exclude as $pattern) {
                $this->patterns->compile($pattern);
            }

            $include = $this->compactIncludes($include);
            $include = array_values(array_filter(
                $include,
                fn (string $path): bool => !$this->isExcludedPath($path, $exclude),
            ));

            if ($include === []) {
                throw new RuntimeException("$tool: effective include cannot be empty.");
            }

            $result[$tool] = new ToolScope($include, $exclude);
        }

        return $result;
    }

    /**
     * Normalizes strings into a sorted unique list.
     *
     * @param list<string> $values Values to normalize.
     * @return list<string> Sorted values with duplicates removed.
     */
    private function stringSet(array $values): array
    {
        $values = array_values(array_unique($values));
        sort($values, SORT_STRING);

        return $values;
    }

    /**
     * Removes child includes when a parent directory already covers them.
     *
     * @param list<string> $paths Include paths to compact.
     * @return list<string> Include paths with redundant children removed.
     */
    private function compactIncludes(array $paths): array
    {
        return array_values(array_filter($paths, static function (string $path) use ($paths): bool {
            foreach ($paths as $parent) {
                if ($path !== $parent && !str_ends_with($parent, '.php') && str_starts_with($path, $parent . '/')) {
                    $relative = substr($path, strlen($parent) + 1);
                    foreach (explode('/', $relative) as $segment) {
                        if (str_starts_with($segment, '.')) {
                            continue 2;
                        }
                    }

                    return false;
                }
            }

            return true;
        }));
    }

    /**
     * Checks whether a literal path is matched by any exclude pattern.
     *
     * @param string $path Literal path to test.
     * @param list<string> $exclude Exclude patterns to evaluate.
     * @return bool True when the path is excluded.
     */
    private function isExcludedPath(string $path, array $exclude): bool
    {
        foreach ($exclude as $pattern) {
            if ($this->patterns->matchesPath($pattern, $path)) {
                return true;
            }
        }

        return false;
    }
}
