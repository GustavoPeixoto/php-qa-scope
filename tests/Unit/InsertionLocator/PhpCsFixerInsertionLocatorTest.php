<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit\InsertionLocator;

use GustavoPeixoto\PhpQaScope\Block\BlockLocator;
use GustavoPeixoto\PhpQaScope\InsertionLocator\InsertionLocatorRegistry;
use GustavoPeixoto\PhpQaScope\InsertionLocator\PhpCsFixerInsertionLocator;
use GustavoPeixoto\PhpQaScope\Scope\ToolScope;
use GustavoPeixoto\PhpQaScope\Target\TargetInitializer;
use GustavoPeixoto\PhpQaScope\Target\TargetInspector;
use GustavoPeixoto\PhpQaScope\Target\TargetRegistry;
use GustavoPeixoto\PhpQaScope\Target\TargetWriter;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use GustavoPeixoto\PhpQaScope\Tool;
use RuntimeException;

/**
 * Verifies safe PHP insertion after declarations without evaluating native code.
 */
final class PhpCsFixerInsertionLocatorTest extends TestCase
{
    /**
     * Inserts after strict-types and other initial declarations and remains valid PHP.
     */
    public function testInsertsAfterLeadingDeclarationsAndSyncRemainsValidPhp(): void
    {
        foreach (["\n", "\r\n"] as $eol) {
            $root = $this->tempRoot();
            $prefix = '<?php' . $eol . '/* header */' . $eol
                . 'declare(strict_types=1);' . $eol . 'declare(ticks=1);';
            $suffix = $eol . '$finder = "old finder";' . $eol . 'return $finder;' . $eol;
            $before = $prefix . $suffix;
            $this->put($root, 'php-cs-fixer.dist.php', $before);
            $targetInitializer = new TargetInitializer(
                locators: new InsertionLocatorRegistry(['php-cs-fixer' => new PhpCsFixerInsertionLocator()]),
                targets: TargetRegistry::default(),
                blockLocator: new BlockLocator(),
                writer: new TargetWriter(),
            );

            self::assertTrue($targetInitializer->insert($root, Tool::PhpCsFixer));
            $pair = $eol . '// php-qa-scope:start' . $eol . '// php-qa-scope:end' . $eol;
            self::assertSame($prefix . $pair . $suffix, file_get_contents($root . '/php-cs-fixer.dist.php'));

            $inspection = TargetInspector::default()->inspect($root, Tool::PhpCsFixer, new ToolScope(['src'], []));
            (new TargetWriter())->write(
                $root,
                $inspection->target->path,
                $inspection->before,
                $inspection->replacement(),
            );
            $after = (string)file_get_contents($root . '/php-cs-fixer.dist.php');
            self::assertStringStartsWith($prefix . $eol, $after);
            self::assertStringEndsWith($suffix, $after);
            self::assertSame(0, $this->process(['php', '-l', $root . '/php-cs-fixer.dist.php'], $root)['code']);
        }
    }

    /**
     * Never executes native code while locating or inserting a managed pair.
     */
    public function testDoesNotExecuteTheConfiguration(): void
    {
        $root = $this->tempRoot();
        $before = "<?php\n// namespace words are comments\n"
            . "file_put_contents(__DIR__ . '/side-effect', 'executed');\nreturn null;\n";
        $this->put($root, 'php-cs-fixer.dist.php', $before);
        $targetInitializer = new TargetInitializer(
            locators: new InsertionLocatorRegistry(['php-cs-fixer' => new PhpCsFixerInsertionLocator()]),
            targets: TargetRegistry::default(),
            blockLocator: new BlockLocator(),
            writer: new TargetWriter(),
        );

        self::assertTrue($targetInitializer->insert($root, Tool::PhpCsFixer));
        self::assertFileDoesNotExist($root . '/side-effect');
        self::assertStringEndsWith(
            substr($before, strlen("<?php\n")),
            (string)file_get_contents($root . '/php-cs-fixer.dist.php'),
        );
    }

    /**
     * Leaves namespace, mixed-content, malformed, and block-declaration files untouched.
     */
    public function testRejectsUnsupportedPhpLayouts(): void
    {
        $files = [
            'not PHP',
            '<?= 1 ?>',
            '<?php namespace App; return null;',
            '<?php return null; ?>html',
            '<?php declare(ticks=1) { return null; }',
            '<?php return (',
            '<?php return null; ?><?php return null;',
        ];
        foreach ($files as $before) {
            $root = $this->tempRoot();
            $this->put($root, 'php-cs-fixer.dist.php', $before);
            $targetInitializer = new TargetInitializer(
                locators: new InsertionLocatorRegistry(['php-cs-fixer' => new PhpCsFixerInsertionLocator()]),
                targets: TargetRegistry::default(),
                blockLocator: new BlockLocator(),
                writer: new TargetWriter(),
            );

            try {
                $targetInitializer->insert($root, Tool::PhpCsFixer);
                self::fail('Unsupported PHP requires manual placement.');
            } catch (RuntimeException $error) {
                self::assertStringContainsString('Place the markers manually', $error->getMessage());
            }
            self::assertSame($before, file_get_contents($root . '/php-cs-fixer.dist.php'));
        }
    }
}
