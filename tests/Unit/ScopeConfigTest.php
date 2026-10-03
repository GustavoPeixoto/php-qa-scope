<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit;

use GustavoPeixoto\PhpQaScope\Scope\ScopeConfig;
use GustavoPeixoto\PhpQaScope\Scope\ToolScope;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use GustavoPeixoto\PhpQaScope\Tool;
use RuntimeException;

/**
 * Covers typed tool selection and validation for directly supplied configurations.
 */
final class ScopeConfigTest extends TestCase
{
    /**
     * Retains caller order and canonical string keys without adding omitted tools.
     */
    public function testPreservesSelectedToolOrder(): void
    {
        $local = new ToolScope([], []);
        $config = new ScopeConfig(['src'], [], ['php-cs-fixer' => $local, 'phpcs' => $local]);

        self::assertSame([Tool::PhpCsFixer, Tool::Phpcs], $config->managedTools());
        self::assertSame(['php-cs-fixer', 'phpcs'], array_keys($config->tools));
        self::assertSame($local, $config->tool(Tool::Phpcs));
    }

    /**
     * Rejects unsupported keys before callers enumerate tools.
     */
    public function testRejectsUnknownToolAtConstruction(): void
    {
        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage("tools: unknown key 'phpmd'.");
        new ScopeConfig(['src'], [], ['phpmd' => new ToolScope([], [])]);
    }

    /**
     * Retains the canonical identifier in errors for an omitted managed tool.
     */
    public function testRejectsUnmanagedTool(): void
    {
        $config = new ScopeConfig(['src'], [], []);
        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage("Tool 'phpstan' is not managed.");
        $config->tool(Tool::Phpstan);
    }
}
