<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Target;

use GustavoPeixoto\PhpQaScope\Tool;
use RuntimeException;

/**
 * Resolves managed tool names to native configuration targets.
 */
final class TargetRegistry
{
    /**
     * Creates a registry from target definitions with matching canonical tool keys.
     *
     * @param array<string, TargetFile> $targets Target files indexed by tool backing value.
     */
    public function __construct(private readonly array $targets)
    {
        foreach ($targets as $tool => $target) {
            if ($tool !== $target->tool->value) {
                throw new RuntimeException(
                    sprintf("Target key '%s' does not match tool '%s'.", $tool, $target->tool->value),
                );
            }
        }
    }

    /**
     * Builds the supported native target definitions in discovery order.
     *
     * @return self Registry containing the built-in target definitions.
     */
    public static function default(): self
    {
        return new self([
            Tool::Phpcs->value => new TargetFile(Tool::Phpcs, 'phpcs.xml', '<!-- php-qa-scope:%s -->', '    '),
            Tool::Phpstan->value => new TargetFile(Tool::Phpstan, 'phpstan.neon', '# php-qa-scope:%s', '    '),
            Tool::PhpCsFixer->value => new TargetFile(
                Tool::PhpCsFixer,
                'php-cs-fixer.dist.php',
                '// php-qa-scope:%s',
                '',
            ),
        ]);
    }

    /**
     * Returns the target file registered for a tool.
     *
     * @param Tool $tool Tool name to resolve.
     * @return TargetFile Native configuration target for the tool.
     */
    public function get(Tool $tool): TargetFile
    {
        return $this->targets[$tool->value] ?? throw new RuntimeException(
            sprintf("No target registered for '%s'.", $tool->value),
        );
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
