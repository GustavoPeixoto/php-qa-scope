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
        self::assertStringContainsString('ERROR Usage: php-qa-scope <init|sync|check>', stream_get_contents($err));
    }

    /**
     * Dispatches init rather than returning usage, and still rejects extra arguments.
     */
    public function testDispatchesInitAndRejectsExtraArguments(): void
    {
        $root = $this->tempRoot();
        $app = Application::default();
        $stderr = fopen('php://memory', 'w+');
        self::assertSame(ExitCode::ERROR, $app->run(['php-qa-scope', 'init'], $root, null, $stderr));
        rewind($stderr);
        self::assertStringContainsString('No supported QA configuration', stream_get_contents($stderr));

        $stderr = fopen('php://memory', 'w+');
        self::assertSame(ExitCode::ERROR, $app->run(['php-qa-scope', 'init', 'extra'], $root, null, $stderr));
        rewind($stderr);
        self::assertStringContainsString('Usage: php-qa-scope <init|sync|check>', stream_get_contents($stderr));
    }

    /**
     * Runs initialization through the package executable from a consumer project root.
     */
    public function testExecutableAcceptsInit(): void
    {
        $root = $this->tempRoot();
        $this->put($root, 'phpstan.neon', "parameters:\n    level: 6\n");
        $result = $this->process(['php', dirname(__DIR__, 2) . '/bin/php-qa-scope', 'init'], $root);

        self::assertSame(ExitCode::SUCCESS, $result['code']);
        self::assertSame("UPDATED phpstan.neon\n", $result['stdout']);
        self::assertFileExists($root . '/php-qa-scope.yml');
    }
}
