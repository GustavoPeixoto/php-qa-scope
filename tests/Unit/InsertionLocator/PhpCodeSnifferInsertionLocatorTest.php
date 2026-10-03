<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit\InsertionLocator;

use GustavoPeixoto\PhpQaScope\Block\BlockLocator;
use GustavoPeixoto\PhpQaScope\InsertionLocator\InsertionLocatorRegistry;
use GustavoPeixoto\PhpQaScope\InsertionLocator\PhpCodeSnifferInsertionLocator;
use GustavoPeixoto\PhpQaScope\Target\TargetInitializer;
use GustavoPeixoto\PhpQaScope\Target\TargetRegistry;
use GustavoPeixoto\PhpQaScope\Target\TargetWriter;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use GustavoPeixoto\PhpQaScope\Tool;
use RuntimeException;

/**
 * Covers conventional PHPCS insertion boundaries and untouched outside XML.
 */
final class PhpCodeSnifferInsertionLocatorTest extends TestCase
{
    /**
     * Skips comments and processing instructions and respects quoted tag delimiters.
     */
    public function testFindsTheActualRulesetOpeningElement(): void
    {
        $prefix = '<?xml version="1.0"?>' . "\n<!-- <ruleset name='fake'> -->\n";
        $opening = "<ruleset\n name=\"App > scope\" description='quoted > delimiter'>";
        $xml = $prefix . $opening . '<file>app</file><rule ref="PSR12"/></ruleset>';

        self::assertSame(strlen($prefix . $opening), (new PhpCodeSnifferInsertionLocator())->locate($xml));
    }

    /**
     * Inserts a valid empty pair in same-line XML without changing original bytes.
     */
    public function testPreservesSameLineContentsAndCrLf(): void
    {
        foreach (["\n", "\r\n"] as $eol) {
            $root = $this->tempRoot();
            $before = '<?xml version="1.0"?>' . $eol
                . '<ruleset name="App"><file>app</file><rule ref="PSR12"/></ruleset>' . $eol;
            $this->put($root, 'phpcs.xml', $before);
            $targetInitializer = new TargetInitializer(
                locators: new InsertionLocatorRegistry(['phpcs' => new PhpCodeSnifferInsertionLocator()]),
                targets: TargetRegistry::default(),
                blockLocator: new BlockLocator(),
                writer: new TargetWriter(),
            );

            self::assertTrue($targetInitializer->insert($root, Tool::Phpcs));
            $after = (string) file_get_contents($root . '/phpcs.xml');
            $pair = $eol . '    <!-- php-qa-scope:start -->' . $eol
                . '    <!-- php-qa-scope:end -->' . $eol;
            self::assertSame($before, str_replace($pair, '', $after));
            self::assertSame(
                '',
                (new BlockLocator())->locate($after, TargetRegistry::default()->get(Tool::Phpcs))->content,
            );
        }
    }

    /**
     * Rejects unsupported or incomplete structures without modifying the file.
     */
    public function testUnsupportedLocationsProvideManualGuidance(): void
    {
        $files = [
            '<ruleset/>',
            '<ruleset />',
            '<other/>',
            '<!-- <ruleset>',
            '<ruleset name="unterminated>',
            '<!DOCTYPE ruleset [<!ELEMENT ruleset ANY>]><ruleset></ruleset>',
        ];
        foreach ($files as $before) {
            $root = $this->tempRoot();
            $this->put($root, 'phpcs.xml', $before);
            $targetInitializer = new TargetInitializer(
                locators: new InsertionLocatorRegistry(['phpcs' => new PhpCodeSnifferInsertionLocator()]),
                targets: TargetRegistry::default(),
                blockLocator: new BlockLocator(),
                writer: new TargetWriter(),
            );

            try {
                $targetInitializer->insert($root, Tool::Phpcs);
                self::fail('Unsupported XML must require manual placement.');
            } catch (RuntimeException $error) {
                self::assertStringContainsString('Place the markers manually', $error->getMessage());
            }
            self::assertSame($before, file_get_contents($root . '/phpcs.xml'));
        }
    }
}
