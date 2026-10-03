<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit\InsertionLocator;

use GustavoPeixoto\PhpQaScope\Block\BlockLocator;
use GustavoPeixoto\PhpQaScope\InsertionLocator\InsertionLocatorRegistry;
use GustavoPeixoto\PhpQaScope\InsertionLocator\PhpStanInsertionLocator;
use GustavoPeixoto\PhpQaScope\Target\TargetInitializer;
use GustavoPeixoto\PhpQaScope\Target\TargetRegistry;
use GustavoPeixoto\PhpQaScope\Target\TargetWriter;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use GustavoPeixoto\PhpQaScope\Tool;
use RuntimeException;

/**
 * Covers PHPStan insertion under a conventional top-level parameters header.
 */
final class PhpStanInsertionLocatorTest extends TestCase
{
    /**
     * Preserves existing parameters and comments with both supported newline styles.
     */
    public function testInsertsUnderTheHeaderAndPreservesParameters(): void
    {
        foreach (["\n", "\r\n"] as $eol) {
            $root = $this->tempRoot();
            $prefix = '# consumer comment' . $eol . 'parameters: # configuration' . $eol;
            $body = '    level: 6' . $eol . '    paths: [app]' . $eol . '    excludePaths: [legacy]' . $eol;
            $before = $prefix . $body;
            $this->put($root, 'phpstan.neon', $before);
            $targetInitializer = new TargetInitializer(
                locators: new InsertionLocatorRegistry(['phpstan' => new PhpStanInsertionLocator()]),
                targets: TargetRegistry::default(),
                blockLocator: new BlockLocator(),
                writer: new TargetWriter(),
            );

            self::assertTrue($targetInitializer->insert($root, Tool::Phpstan));
            $pair = '    # php-qa-scope:start' . $eol . '    # php-qa-scope:end' . $eol;
            self::assertSame($prefix . $pair . $body, file_get_contents($root . '/phpstan.neon'));
        }
    }

    /**
     * Supports an empty parameters block at EOF or before another root section.
     */
    public function testSupportsAnEmptyParametersBlock(): void
    {
        $locator = new PhpStanInsertionLocator();
        self::assertSame(strlen('parameters:'), $locator->locate('parameters:'));
        self::assertSame(strlen("parameters:\n"), $locator->locate("parameters:\n# comment\nservices:\n    - App\n"));
    }

    /**
     * Rejects absent, nested, inline, duplicated, and incompatible indentation layouts.
     */
    public function testRejectsUnsupportedLayoutsWithoutWriting(): void
    {
        $contents = [
            "includes:\n    - base.neon\n",
            "outer:\n    parameters:\n        level: 6\n",
            "parameters: {}\n",
            "parameters: []\n",
            "parameters:\n    level: 6\nparameters:\n    paths: [src]\n",
            "parameters:\n    level: 6\n'parameters': {}\n",
            "parameters:\n  level: 6\n",
            "parameters:\n\tlevel: 6\n",
        ];
        foreach ($contents as $before) {
            $root = $this->tempRoot();
            $this->put($root, 'phpstan.neon', $before);
            $targetInitializer = new TargetInitializer(
                locators: new InsertionLocatorRegistry(['phpstan' => new PhpStanInsertionLocator()]),
                targets: TargetRegistry::default(),
                blockLocator: new BlockLocator(),
                writer: new TargetWriter(),
            );

            try {
                $targetInitializer->insert($root, Tool::Phpstan);
                self::fail('Unsupported layouts require manual placement.');
            } catch (RuntimeException $error) {
                self::assertStringContainsString('Place the markers manually', $error->getMessage());
            }
            self::assertSame($before, file_get_contents($root . '/phpstan.neon'));
        }
    }
}
