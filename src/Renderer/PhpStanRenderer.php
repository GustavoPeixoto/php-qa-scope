<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Renderer;

use GustavoPeixoto\PhpQaScope\Config\ToolScope;
use GustavoPeixoto\PhpQaScope\Glob\PatternCompiler;

/**
 * Renders managed PHPStan path configuration.
 */
final class PhpStanRenderer implements Renderer
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
     * Renders the managed PHPStan block for a tool scope.
     *
     * @param ToolScope $scope Scope to render into PHPStan NEON.
     * @return string NEON fragment for the managed scope block.
     */
    public function render(ToolScope $scope): string
    {
        $lines = ['    paths:'];
        foreach ($scope->include as $path) {
            $lines[] = "        - '$path'";
        }

        $lines[] = '    excludePaths:';
        $lines[] = '        analyse:' . ($scope->exclude === [] ? ' []' : '');

        $excludes = [];
        foreach ($scope->exclude as $pattern) {
            $compiled = $this->patterns->compile($pattern);
            foreach ($compiled->phpStanPaths as $path) {
                $excludes[] = "            - '$path'" . ($compiled->optionalForPhpStan ? ' (?)' : '');
            }
        }

        return implode("\n", [...$lines, ...array_unique($excludes)]) . "\n";
    }
}
