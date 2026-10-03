<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit\Cli;

use GustavoPeixoto\PhpQaScope\Application;
use GustavoPeixoto\PhpQaScope\Cli\ExitCode;
use GustavoPeixoto\PhpQaScope\Cli\Input;
use GustavoPeixoto\PhpQaScope\Command\Command;
use GustavoPeixoto\PhpQaScope\Command\CommandRegistry;
use GustavoPeixoto\PhpQaScope\Console\Console;
use GustavoPeixoto\PhpQaScope\Console\ConsoleWriter;
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
        $input = Input::fromArgv(['php-qa-scope', 'check'], 'custom usage', '/repo');
        $console = new ConsoleWriter();
        $console->line('OK phpstan.neon');
        $console->errorLine('ERROR no');

        self::assertSame('check', $input->command);
        self::assertSame('/repo', $input->root);
        self::assertSame("OK phpstan.neon\n", $console->stdout());
        self::assertSame("ERROR no\n", $console->stderr());
    }

    /**
     * Rejects extra arguments with the caller-supplied usage text.
     */
    public function testRejectsInvalidArgumentCount(): void
    {
        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage('custom usage');
        Input::fromArgv(['php-qa-scope', 'check', 'extra'], 'custom usage', '/repo');
    }

    /**
     * Verifies unknown commands produce an application error result.
     */
    public function testApplicationReturnsErrorForUnknownCommand(): void
    {
        $app = Application::default();
        $stderr = fopen('php://memory', 'w+');

        $code = $app->run(
            [
                'php-qa-scope',
                'invalid',
            ],
            new Console(new ConsoleWriter(null, $stderr)),
            $this->tempRoot(),
        );

        rewind($stderr);
        self::assertSame(ExitCode::ERROR, $code);
        self::assertStringContainsString('ERROR Usage: php-qa-scope <init|sync|check>', stream_get_contents($stderr));
    }

    /**
     * Dispatches init rather than returning usage, and still rejects extra arguments.
     */
    public function testDispatchesInitAndRejectsExtraArguments(): void
    {
        $root = $this->tempRoot();
        $app = Application::default();
        $stderr = fopen('php://memory', 'w+');
        self::assertSame(
            ExitCode::ERROR,
            $app->run(['php-qa-scope', 'init'], new Console(new ConsoleWriter(null, $stderr)), $root),
        );
        rewind($stderr);
        self::assertStringContainsString('No supported QA configuration', stream_get_contents($stderr));

        $stderr = fopen('php://memory', 'w+');
        self::assertSame(
            ExitCode::ERROR,
            $app->run(['php-qa-scope', 'init', 'extra'], new Console(new ConsoleWriter(null, $stderr)), $root),
        );
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
        $result = $this->process(['php', dirname(__DIR__, 3) . '/bin/php-qa-scope', 'init'], $root);

        self::assertSame(ExitCode::SUCCESS, $result['code']);
        self::assertSame("UPDATED phpstan.neon\n", $result['stdout']);
        self::assertFileExists($root . '/php-qa-scope.yml');
    }

    /**
     * Normalizes missing names and retains unknown names for registry validation.
     */
    public function testParsesMissingAndUnknownCommands(): void
    {
        foreach ([[], ['php-qa-scope']] as $argv) {
            $input = Input::fromArgv($argv, 'custom usage', '/repo');
            self::assertSame('', $input->command);
            self::assertSame('/repo', $input->root);
        }
        $unknown = Input::fromArgv(['php-qa-scope', 'unknown'], 'custom usage', '/repo');
        self::assertSame('unknown', $unknown->command);
        self::assertSame('/repo', $unknown->root);
    }

    /**
     * Uses the same supplied command list for all usage errors without dispatch.
     */
    public function testCustomRegistryUsageForAllInvalidInputs(): void
    {
        $commands = [];
        foreach (['sync', 'check'] as $name) {
            $command = $this->createMock(Command::class);
            $command->method('name')->willReturn($name);
            $command->expects(self::never())->method('execute');
            $commands[] = $command;
        }
        $app = new Application(new CommandRegistry($commands));
        $arguments = [
            [],
            ['php-qa-scope'],
            [
                'php-qa-scope',
                'unknown',
            ],
            [
                'php-qa-scope',
                'sync',
                'extra',
            ],
        ];
        foreach ($arguments as $argv) {
            $stderr = fopen('php://memory', 'w+');
            self::assertSame(ExitCode::ERROR, $app->run($argv, new Console(new ConsoleWriter(null, $stderr)), '/repo'));
            rewind($stderr);
            self::assertSame("ERROR Usage: php-qa-scope <sync|check>\n", stream_get_contents($stderr));
            fclose($stderr);
        }
    }

    /**
     * Preserves default usage output when the missing command reaches the registry.
     */
    public function testDefaultApplicationRejectsMissingCommands(): void
    {
        $app = Application::default();
        foreach ([[], ['php-qa-scope']] as $argv) {
            $stderr = fopen('php://memory', 'w+');
            self::assertSame(ExitCode::ERROR, $app->run($argv, new Console(new ConsoleWriter(null, $stderr)), '/repo'));
            rewind($stderr);
            self::assertSame("ERROR Usage: php-qa-scope <init|sync|check>\n", stream_get_contents($stderr));
            fclose($stderr);
        }
    }
}
