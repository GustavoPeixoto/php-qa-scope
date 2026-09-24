<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit;

use GustavoPeixoto\PhpQaScope\Application;
use GustavoPeixoto\PhpQaScope\Cli\ExitCode;
use GustavoPeixoto\PhpQaScope\Cli\Input;
use GustavoPeixoto\PhpQaScope\Cli\Output;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use RuntimeException;

/**
 * Covers CLI input parsing, output buffering, and application error handling.
 */
final class CliTest extends TestCase
{
    /**
     * Verifies CLI input parsing and buffered output behavior.
     */
    public function testParsesInputAndBuffersOutput(): void
    {
        $input = Input::fromArgv(['php-qa-scope', 'check'], '/repo');
        $output = new Output();
        $output->line('OK phpstan.neon');
        $output->errorLine('ERROR no');

        self::assertSame('check', $input->command);
        self::assertSame('/repo', $input->root);
        self::assertSame("OK phpstan.neon\n", $output->stdout());
        self::assertSame("ERROR no\n", $output->stderr());
    }

    /**
     * Verifies invalid argument counts are rejected.
     */
    public function testRejectsInvalidArgumentCount(): void
    {
        $this->expectException(RuntimeException::class);
        Input::fromArgv(['php-qa-scope', 'check', 'extra'], '/repo');
    }

    /**
     * Verifies unknown commands produce an application error result.
     */
    public function testApplicationReturnsErrorForUnknownCommand(): void
    {
        $app = Application::default();
        $err = fopen('php://memory', 'w+');

        $code = $app->run(['php-qa-scope', 'invalid'], $this->tempRoot(), null, $err);

        rewind($err);
        self::assertSame(ExitCode::ERROR, $code);
        self::assertStringContainsString('ERROR Usage: php-qa-scope <sync|check>', stream_get_contents($err));
    }
}
