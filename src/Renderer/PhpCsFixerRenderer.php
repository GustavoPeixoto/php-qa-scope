<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Renderer;

use GustavoPeixoto\PhpQaScope\Config\ToolScope;
use GustavoPeixoto\PhpQaScope\Glob\PatternCompiler;
use SplFileInfo;

/**
 * Renders managed PHP-CS-Fixer finder configuration.
 */
final class PhpCsFixerRenderer implements Renderer
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
     * Renders the managed PHP-CS-Fixer block for a tool scope.
     *
     * @param ToolScope $scope Scope to render into finder PHP code.
     * @return string PHP code fragment for the managed scope block.
     */
    public function render(ToolScope $scope): string
    {
        $directories = [];
        $files = [];

        foreach ($scope->include as $path) {
            $expression = "__DIR__ . '/$path'";
            if (str_ends_with($path, '.php')) {
                $files[] = '    new ' . SplFileInfo::class . "($expression),";
            } else {
                $directories[] = "        $expression,";
            }
        }

        $lines = [
            '$finder = Symfony\\Component\\Finder\\Finder::create()',
            '    ->files()',
            "    ->name('/\\.php$/')",
            '    ->ignoreDotFiles(true)',
            '    ->ignoreVCS(false)',
        ];

        if ($directories !== []) {
            $lines = [...$lines, '    ->in([', ...$directories, '    ])'];
        }

        $lines[count($lines) - 1] .= ';';

        if ($files !== []) {
            $lines = [...$lines, '$finder->append([', ...$files, ']);'];
        }

        if ($scope->exclude !== []) {
            $patterns = array_map(
                fn (string $pattern): string => $this->patterns->compile($pattern)->regex,
                $scope->exclude,
            );
            $regex = '~^(?:' . implode('|', $patterns) . ')~D';
            $lines = [
                ...$lines,
                '$finder = new CallbackFilterIterator(',
                '    $finder->getIterator(),',
                '    static function (SplFileInfo $file): bool {',
                "        \$path = substr(str_replace('\\\\', '/', \$file->getPathname()), strlen(__DIR__) + 1);",
                '',
                '        return preg_match(' . var_export($regex, true) . ', $path) !== 1;',
                '    },',
                ');',
            ];
        }

        return implode("\n", $lines) . "\n\n";
    }
}
