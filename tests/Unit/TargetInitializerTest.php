<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit;

use GustavoPeixoto\PhpQaScope\Block\BlockLocator;
use GustavoPeixoto\PhpQaScope\InsertionLocator\InsertionLocator;
use GustavoPeixoto\PhpQaScope\InsertionLocator\InsertionLocatorRegistry;
use GustavoPeixoto\PhpQaScope\Target\TargetInitializer;
use GustavoPeixoto\PhpQaScope\Target\TargetRegistry;
use GustavoPeixoto\PhpQaScope\Target\TargetWriter;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use GustavoPeixoto\PhpQaScope\Tool;
use RuntimeException;

/**
 * Verifies strict marker classification and persisted empty-pair preparation.
 */
final class TargetInitializerTest extends TestCase
{
    /**
     * Persists an empty pair without rendering and preserves outside bytes and mode.
     */
    public function testPersistsAnEmptyPairAndPreservesOutsideContent(): void
    {
        $root = $this->tempRoot();
        $before = "parameters:\r\n    level: 6\r\n";
        $this->put($root, 'phpstan.neon', $before);
        chmod($root . '/phpstan.neon', 0640);
        $targetInitializer = $this->preparer();

        self::assertTrue($targetInitializer->insert($root, Tool::Phpstan));
        $after = (string) file_get_contents($root . '/phpstan.neon');
        $pair = "    # php-qa-scope:start\r\n    # php-qa-scope:end\r\n";
        self::assertSame($before, str_replace($pair, '', $after));
        self::assertSame(0640, fileperms($root . '/phpstan.neon') & 0777);
        $block = (new BlockLocator())->locate($after, TargetRegistry::default()->get(Tool::Phpstan));
        self::assertSame('', $block->content);

        $inode = fileinode($root . '/phpstan.neon');
        self::assertFalse($targetInitializer->insert($root, Tool::Phpstan));
        clearstatcache(true, $root . '/phpstan.neon');
        self::assertSame($inode, fileinode($root . '/phpstan.neon'));
    }

    /**
     * Preserves a valid pre-existing divergent block for the later sync phase.
     */
    public function testPreservesExistingBlockBytes(): void
    {
        $root = $this->tempRoot();
        $before = "parameters:\n    # php-qa-scope:start\n    paths: [app]\n    # php-qa-scope:end\n";
        $this->put($root, 'phpstan.neon', $before);

        self::assertFalse($this->preparer()->insert($root, Tool::Phpstan));
        self::assertSame($before, file_get_contents($root . '/phpstan.neon'));
    }

    /**
     * Rejects incomplete, duplicate, reversed, malformed, and incorrectly indented pairs.
     */
    public function testRejectsInvalidExistingMarkersWithoutChangingFiles(): void
    {
        $pairs = [
            "    # php-qa-scope:start\n",
            "    # php-qa-scope:end\n",
            "    # php-qa-scope:start\n    # php-qa-scope:start\n    # php-qa-scope:end\n",
            "    # php-qa-scope:start\n    # php-qa-scope:end\n    # php-qa-scope:end\n",
            "    # php-qa-scope:end\n    # php-qa-scope:start\n",
            "    // php-qa-scope:start\n    // php-qa-scope:end\n",
            "  # php-qa-scope:start\n  # php-qa-scope:end\n",
        ];
        foreach ($pairs as $pair) {
            $root = $this->tempRoot();
            $before = "parameters:\n" . $pair;
            $this->put($root, 'phpstan.neon', $before);

            try {
                $this->preparer()->insert($root, Tool::Phpstan);
                self::fail('An invalid marker state must not be repaired.');
            } catch (RuntimeException $error) {
                self::assertStringContainsString('phpstan.neon:', $error->getMessage());
            }
            self::assertSame($before, file_get_contents($root . '/phpstan.neon'));
        }
    }

    /**
     * Reports missing insertion strategies without changing the native file.
     */
    public function testMissingInsertionStrategyProvidesManualPlacementGuidance(): void
    {
        $root = $this->tempRoot();
        $before = "parameters:\n    level: 6\n";
        $this->put($root, 'phpstan.neon', $before);
        $targetInitializer = new TargetInitializer(
            new InsertionLocatorRegistry([]),
            targets: TargetRegistry::default(),
            blockLocator: new BlockLocator(),
            writer: new TargetWriter(),
        );

        try {
            $targetInitializer->insert($root, Tool::Phpstan);
            self::fail('A missing insertion strategy must be reported.');
        } catch (RuntimeException $error) {
            self::assertStringContainsString('phpstan.neon:', $error->getMessage());
            self::assertStringContainsString("No insertion locator registered for 'phpstan'.", $error->getMessage());
            self::assertStringContainsString('Place the markers manually', $error->getMessage());
            self::assertStringContainsString('#managed-blocks', $error->getMessage());
        }

        self::assertSame($before, file_get_contents($root . '/phpstan.neon'));
        self::assertSame([], glob($root . '/.php-qa-scope-*'));
    }

    /**
     * Creates a preparer with a controlled insertion boundary for classification tests.
     *
     * @return TargetInitializer Preparation workflow for a parameters header.
     */
    private function preparer(): TargetInitializer
    {
        $locator = new class () implements InsertionLocator {
            /**
             * Inserts after a parameters header in the test fixture.
             *
             * @param string $contents Original fixture bytes.
             * @return int Offset after the header's first newline.
             */
            public function locate(string $contents): int
            {
                return (int) strpos($contents, "\n") + 1;
            }
        };

        return new TargetInitializer(
            locators: new InsertionLocatorRegistry(['phpstan' => $locator]),
            targets: TargetRegistry::default(),
            blockLocator: new BlockLocator(),
            writer: new TargetWriter(),
        );
    }
}
