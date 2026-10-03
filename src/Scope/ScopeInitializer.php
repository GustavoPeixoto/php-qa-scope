<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Scope;

use RuntimeException;
use Symfony\Component\Yaml\Yaml;

/**
 * Commits a complete scope YAML only if its destination is still absent.
 */
final class ScopeInitializer
{
    /**
     * Creates the YAML using an atomic create-only link to a prepared file.
     *
     * @param string $root Project root where the YAML will be created.
     * @param array<string, \GustavoPeixoto\PhpQaScope\Target\TargetFile> $tools Discovered native targets indexed by tool name.
     */
    public function create(string $root, array $tools): void
    {
        if (!$this->validate($root)) {
            return;
        }
        $contents = $this->contents($tools);

        $temp = tempnam($root, '.php-qa-scope-');
        if ($temp === false) {
            throw new RuntimeException('php-qa-scope.yml: could not create a temporary file.');
        }

        try {
            if (
                file_put_contents($temp, $contents) !== strlen($contents)
                || !chmod($temp, 0666 & ~umask())
            ) {
                throw new RuntimeException('php-qa-scope.yml: failed to prepare the scope configuration.');
            }
            if (!@link($temp, $root . '/php-qa-scope.yml')) {
                throw new RuntimeException(
                    'php-qa-scope.yml: could not create the scope configuration; '
                    . 'the destination may have appeared during init. Run again.',
                );
            }
        } finally {
            if (is_file($temp)) {
                unlink($temp);
            }
        }
    }

    /**
     * Rejects unsafe destinations and determines whether YAML creation is needed.
     *
     * @param string $root Project root where the YAML will be created.
     *
     * @return bool Whether the YAML destination is absent and can be created.
     */
    private function validate(string $root): bool
    {
        $file = $root . '/php-qa-scope.yml';
        clearstatcache(true, $file);
        if (is_link($file)) {
            throw new RuntimeException('php-qa-scope.yml: scope configuration cannot be a symbolic link.');
        }
        if (file_exists($file)) {
            return false;
        }
        if (!is_dir($root) || !is_writable($root)) {
            throw new RuntimeException('php-qa-scope.yml: could not create the scope configuration.');
        }

        return true;
    }

    /**
     * Generates default YAML from the already discovered managed tools.
     *
     * @param array<string, \GustavoPeixoto\PhpQaScope\Target\TargetFile> $tools Discovered native targets indexed by tool name.
     *
     * @return string Complete default scope YAML with empty scope sequences.
     */
    private function contents(array $tools): string
    {
        $defaults = [];
        foreach (array_keys($tools) as $tool) {
            $defaults[$tool] = [
                'include' => [],
                'exclude' => [],
            ];
        }
        $contents = Yaml::dump(
            [
                'include' => ['src'],
                'exclude' => [],
                'tools' => $defaults
            ],
            5,
            2,
            Yaml::DUMP_EMPTY_ARRAY_AS_SEQUENCE,
        );
        Yaml::parse($contents);

        return $contents;
    }
}
