<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Config;

use GustavoPeixoto\PhpQaScope\Glob\PathValidator;
use RuntimeException;
use Symfony\Component\Yaml\Yaml;

/**
 * Loads and validates php-qa-scope YAML configuration files.
 */
final class ScopeLoader
{
    /**
     * Loads a configuration file from disk.
     *
     * @param string $file Path to the php-qa-scope YAML file.
     * @return ScopeConfig Parsed and validated configuration.
     */
    public function load(string $file): ScopeConfig
    {
        $data = Yaml::parseFile($file);
        $this->validateMap($data, ['include', 'exclude', 'tools'], 'php-qa-scope.yml');

        foreach (['include', 'exclude', 'tools'] as $required) {
            if (!array_key_exists($required, $data)) {
                throw new RuntimeException("php-qa-scope.yml: missing required '$required'.");
            }
        }

        $globalInclude = $this->stringList($data['include'], 'include');
        if ($globalInclude === []) {
            throw new RuntimeException('include: expected at least one path.');
        }

        $globalExclude = $this->stringList($data['exclude'], 'exclude', false);
        $this->validateMap($data['tools'], ScopeConfig::TOOLS, 'tools');

        $tools = [];
        foreach ($data['tools'] as $tool => $local) {
            $this->validateMap($local, ['include', 'exclude'], "tools.$tool");
            foreach (['include', 'exclude'] as $required) {
                if (!array_key_exists($required, $local)) {
                    throw new RuntimeException("tools.$tool: missing required '$required'.");
                }
            }

            $tools[$tool] = new ToolScope(
                $this->stringList($local['include'], "tools.$tool.include"),
                $this->stringList($local['exclude'], "tools.$tool.exclude", false),
            );
        }

        foreach ($globalInclude as $path) {
            PathValidator::literal($path);
        }

        foreach ($globalExclude as $pattern) {
            PathValidator::excludePatternShape($pattern);
        }

        return new ScopeConfig($globalInclude, $globalExclude, $tools);
    }

    /**
     * Ensures that a YAML value is a map with known keys.
     *
     * @param mixed $value Value to validate.
     * @param list<string> $allowed Allowed map keys.
     * @param string $location Human-readable configuration location.
     */
    private function validateMap(mixed $value, array $allowed, string $location): void
    {
        if (!is_array($value) || ($value !== [] && array_is_list($value))) {
            throw new RuntimeException("$location: expected a map.");
        }

        foreach (array_keys($value) as $key) {
            if (!is_string($key) || !in_array($key, $allowed, true)) {
                throw new RuntimeException("$location: unknown key '$key'.");
            }
        }
    }

    /**
     * Normalizes and validates a YAML list of paths or patterns.
     *
     * @param mixed $value Value expected to be a list of strings.
     * @param string $location Human-readable configuration location.
     * @param bool $validateLiteral Whether entries must be literal paths instead of exclude patterns.
     * @return list<string> Sorted unique list of validated entries.
     */
    private function stringList(mixed $value, string $location, bool $validateLiteral = true): array
    {
        if (!is_array($value) || !array_is_list($value)) {
            throw new RuntimeException("$location: expected a list of strings.");
        }

        foreach ($value as $item) {
            if (!is_string($item) || $item === '') {
                throw new RuntimeException("$location: expected a non-empty path.");
            }

            if ($validateLiteral) {
                PathValidator::literal($item);
            } else {
                PathValidator::excludePatternShape($item);
            }
        }

        $value = array_values(array_unique($value));
        sort($value, SORT_STRING);

        return $value;
    }
}
