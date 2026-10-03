<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit\Target;

use GustavoPeixoto\PhpQaScope\Target\TargetWriter;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use RuntimeException;

/**
 * Verifies shared native replacement safeguards independently of rendering.
 */
final class TargetWriterTest extends TestCase
{
    /**
     * Preserves exact replacement bytes and permissions and skips unchanged writes.
     */
    public function testPreservesBytesAndPermissionsAndSkipsUnchangedWrites(): void
    {
        $root = $this->tempRoot();
        $this->put($root, 'phpstan.neon', "parameters:\r\n    level: 6\r\n");
        chmod($root . '/phpstan.neon', 0640);
        $writer = new TargetWriter();
        $before = $writer->read($root, 'phpstan.neon');
        $after = $before . "    # inserted\r\n";
        $writer->write($root, 'phpstan.neon', $before, $after, 'init');

        self::assertSame($after, file_get_contents($root . '/phpstan.neon'));
        self::assertSame(0640, fileperms($root . '/phpstan.neon') & 0777);
        $inode = fileinode($root . '/phpstan.neon');
        $writer->write($root, 'phpstan.neon', $after, $after, 'init');
        clearstatcache(true, $root . '/phpstan.neon');
        self::assertSame($inode, fileinode($root . '/phpstan.neon'));
        self::assertSame([], glob($root . '/.php-qa-scope-*'));
    }

    /**
     * Refuses concurrent native changes and cleans its replacement temporary file.
     */
    public function testConcurrentChangeIsNotOverwritten(): void
    {
        $root = $this->tempRoot();
        $this->put($root, 'phpstan.neon', 'before');
        $writer = new TargetWriter();
        $before = $writer->read($root, 'phpstan.neon');
        $this->put($root, 'phpstan.neon', 'concurrent');

        try {
            $writer->write($root, 'phpstan.neon', $before, 'replacement', 'init');
            self::fail('Concurrent content must not be overwritten.');
        } catch (RuntimeException $error) {
            self::assertStringContainsString('changed during init', $error->getMessage());
        }

        self::assertSame('concurrent', file_get_contents($root . '/phpstan.neon'));
        self::assertSame([], glob($root . '/.php-qa-scope-*'));
    }

    /**
     * Rejects symbolic links for both reading and replacement.
     */
    public function testRejectsSymbolicLinks(): void
    {
        $root = $this->tempRoot();
        $this->put($root, 'actual.neon', 'original');
        symlink($root . '/actual.neon', $root . '/phpstan.neon');
        $writer = new TargetWriter();

        foreach (['read', 'write'] as $operation) {
            try {
                if ($operation === 'read') {
                    $writer->read($root, 'phpstan.neon');
                } else {
                    $writer->write($root, 'phpstan.neon', 'original', 'replacement', 'init');
                }
                self::fail('Symbolic links must be rejected.');
            } catch (RuntimeException $error) {
                self::assertStringContainsString('symbolic links', $error->getMessage());
            }
        }

        self::assertSame('original', file_get_contents($root . '/actual.neon'));
        self::assertTrue(is_link($root . '/phpstan.neon'));
    }
}
