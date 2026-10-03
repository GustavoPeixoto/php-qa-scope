<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit;

use GustavoPeixoto\PhpQaScope\Command\Command;
use GustavoPeixoto\PhpQaScope\Command\CommandRegistry;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use RuntimeException;

/**
 * Covers supplied command resolution and registration-derived usage text.
 */
final class CommandRegistryTest extends TestCase
{
    /**
     * Advertises only supplied commands in registration order and resolves their instances.
     */
    public function testUsageAndResolutionFollowSuppliedCommands(): void
    {
        $sync = $this->createStub(Command::class);
        $sync->method('name')->willReturn('sync');
        $check = $this->createStub(Command::class);
        $check->method('name')->willReturn('check');
        $registry = new CommandRegistry([$sync, $check]);

        self::assertSame('Usage: php-qa-scope <sync|check>', $registry->usage());
        self::assertSame($sync, $registry->get('sync'));
        self::assertSame($check, $registry->get('check'));
    }

    /**
     * Rejects the normalized missing command with this registry's usage text.
     */
    public function testRejectsMissingCommand(): void
    {
        $sync = $this->createStub(Command::class);
        $sync->method('name')->willReturn('sync');
        $registry = new CommandRegistry([$sync]);

        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage('Usage: php-qa-scope <sync>');
        $registry->get('');
    }

    /**
     * Rejects an unregistered command without advertising built-in fallbacks.
     */
    public function testRejectsUnknownCommand(): void
    {
        $sync = $this->createStub(Command::class);
        $sync->method('name')->willReturn('sync');
        $registry = new CommandRegistry([$sync]);

        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage('Usage: php-qa-scope <sync>');
        $registry->get('init');
    }
}
