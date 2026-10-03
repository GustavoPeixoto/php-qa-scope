<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Target;

use RuntimeException;

/**
 * Resolves managed tool names to native configuration targets.
 */
final class TargetRegistry
{
    /** @var array<string, TargetFile> Target files indexed by tool name. */
    private array $targets;

    /**
     * Creates the registry with built-in target definitions.
     */
    public function __construct()
    {
        $this->targets = [
            'phpcs' => new TargetFile('phpcs', 'phpcs.xml', '<!-- php-qa-scope:%s -->', '    '),
            'phpstan' => new TargetFile('phpstan', 'phpstan.neon', '# php-qa-scope:%s', '    '),
            'php-cs-fixer' => new TargetFile('php-cs-fixer', 'php-cs-fixer.dist.php', '// php-qa-scope:%s', ''),
        ];
    }

    /**
     * Returns the target file registered for a tool.
     *
     * @param string $tool Tool name to resolve.
     * @return TargetFile Native configuration target for the tool.
     */
    public function get(string $tool): TargetFile
    {
        return $this->targets[$tool] ?? throw new RuntimeException("No target registered for '$tool'.");
    }

    /**
     * Discovers exact supported native filenames in the project root.
     *
     * @param string $root Project root to inspect without recursive discovery.
     * @return array<string, TargetFile> Existing native files indexed by tool.
     */
    public function discover(string $root): array
    {
        $found = [];
        foreach ($this->targets as $tool => $target) {
            if (is_file($root . '/' . $target->path)) {
                $found[$tool] = $target;
            }
        }

        if ($found === []) {
            throw new RuntimeException(
                'No supported QA configuration found in the project root. '
                . 'Expected phpcs.xml, phpstan.neon, or php-cs-fixer.dist.php.',
            );
        }

        return $found;
    }
}
