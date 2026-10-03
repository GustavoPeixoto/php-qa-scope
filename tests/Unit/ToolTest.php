<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit;

use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use GustavoPeixoto\PhpQaScope\Tool;

/**
 * Covers the supported tool identity and external string conversion contract.
 */
final class ToolTest extends TestCase
{
    /**
     * Preserves the supported cases, backing values, and default vocabulary order.
     */
    public function testSupportedIdentities(): void
    {
        self::assertSame([Tool::Phpcs, Tool::Phpstan, Tool::PhpCsFixer], Tool::cases());
        self::assertSame(['phpcs', 'phpstan', 'php-cs-fixer'], array_column(Tool::cases(), 'value'));
        self::assertSame(Tool::Phpstan, Tool::tryFrom('phpstan'));
    }
}
