<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit;

use GustavoPeixoto\PhpQaScope\Sync\ManagedBlock;
use GustavoPeixoto\PhpQaScope\Sync\TargetFile;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use RuntimeException;

/**
 * Covers managed block marker location and validation.
 */
final class ManagedBlockTest extends TestCase
{
    private TargetFile $target;

    /**
     * Creates the target definition shared by managed block tests.
     */
    protected function setUp(): void
    {
        $this->target = new TargetFile('phpstan', 'phpstan.neon', '# php-qa-scope:%s', '    ');
    }

    /**
     * Verifies valid blocks are located with their original line ending.
     */
    public function testLocatesValidBlockAndPreservesLineEndingSignal(): void
    {
        $text = "parameters:\r\n    # php-qa-scope:start\r\n    paths: []\r\n    # php-qa-scope:end\r\n";
        $block = (new ManagedBlock())->locate($text, $this->target);

        self::assertSame("\r\n", $block->eol);
        self::assertSame("    paths: []\r\n", $block->content);
    }

    /**
     * Verifies invalid marker arrangements are rejected.
     */
    public function testRejectsInvalidBlocks(): void
    {
        $cases = [
            'missing' => "parameters:\n    # php-qa-scope:start\n",
            'duplicate' => "    # php-qa-scope:start\n    # php-qa-scope:end\n    # php-qa-scope:start\n",
            'reversed' => "    # php-qa-scope:end\n    # php-qa-scope:start\n",
            'indent' => "# php-qa-scope:start\n    # php-qa-scope:end\n",
        ];

        foreach ($cases as $text) {
            $exception = null;

            try {
                (new ManagedBlock())->locate($text, $this->target);
            } catch (RuntimeException $error) {
                $exception = $error;
            }

            self::assertInstanceOf(RuntimeException::class, $exception);
        }
    }
}
