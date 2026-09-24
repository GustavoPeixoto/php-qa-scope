<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit;

use GustavoPeixoto\PhpQaScope\Glob\PatternCompiler;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use RuntimeException;

/**
 * Covers supported and unsupported exclude pattern compilation.
 */
final class PatternCompilerTest extends TestCase
{
    /**
     * Verifies supported pattern forms compile to matching regular expressions.
     */
    public function testCompilesSupportedPatternForms(): void
    {
        $cases = [
            ['src/A.php', ['src/A.php'], ['src/A.php.bak', 'other/src/A.php']],
            ['tests/fixtures/**', ['tests/fixtures/A.php', 'tests/fixtures/deep/A.php'], ['tests/fixturesOld/A.php']],
            ['**/legacy/**', ['legacy/A.php', 'src/legacy/A.php', 'src/deep/legacy/A.php'], ['src/legacyOld/A.php']],
            ['config/**/legacy/**', ['config/legacy/A.php', 'config/a/b/legacy/A.php'], ['src/config/legacy/A.php']],
            [
                '**/*Generated.php',
                ['Generated.php', 'src/A Generated.php', 'src/a/BGenerated.php'],
                ['src/Generated.php.bak'],
            ],
        ];

        $compiler = new PatternCompiler();
        foreach ($cases as [$pattern, $matches, $misses]) {
            $regex = '~^' . $compiler->compile($pattern)->regex . '~D';
            foreach ($matches as $path) {
                self::assertSame(1, preg_match($regex, $path), "$pattern should match $path");
            }

            foreach ($misses as $path) {
                self::assertSame(0, preg_match($regex, $path), "$pattern should not match $path");
            }
        }
    }

    /**
     * Verifies unsupported pattern syntax is rejected.
     */
    public function testRejectsUnsupportedSyntax(): void
    {
        $compiler = new PatternCompiler();
        $unsupported = [
            'plugins/*/vendor/**',
            'src/*.php',
            '**/Generated*.php',
            '**/Foo?.php',
            '**/*.{php,inc}',
            '!src/A.php',
            '/src/A.php',
            'src/[A-Z]File.php',
            'tests/fixtures',
        ];

        foreach ($unsupported as $pattern) {
            $exception = null;

            try {
                $compiler->compile($pattern);
            } catch (RuntimeException $error) {
                $exception = $error;
            }

            self::assertInstanceOf(RuntimeException::class, $exception, $pattern);
        }
    }
}
