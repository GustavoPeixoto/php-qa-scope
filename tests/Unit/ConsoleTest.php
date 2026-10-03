<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit;

use GustavoPeixoto\PhpQaScope\Application;
use GustavoPeixoto\PhpQaScope\Cli\ExitCode;
use GustavoPeixoto\PhpQaScope\Cli\Input;
use GustavoPeixoto\PhpQaScope\Command\Command;
use GustavoPeixoto\PhpQaScope\Command\CommandRegistry;
use GustavoPeixoto\PhpQaScope\Console\Console;
use GustavoPeixoto\PhpQaScope\Console\ConsoleWriter;
use GustavoPeixoto\PhpQaScope\Console\ConsoleWriterInterface;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use RuntimeException;

/**
 * Covers console delegation, supplied output graphs, and executable composition.
 */
final class ConsoleTest extends TestCase
{
    /**
     * Forwards each supplied string once without adding formatting or getters.
     */
    public function testFacadeDelegatesUnchangedLines(): void
    {
        $writer = $this->createMock(ConsoleWriterInterface::class);
        $writer->expects(self::once())->method('line')->with("first\nsecond");
        $writer->expects(self::once())->method('errorLine')->with('');
        $console = new Console($writer);

        $console->line("first\nsecond");
        $console->errorLine('');
    }

    /**
     * Keeps mirrored streams identical to the writer's accumulated buffers.
     */
    public function testWriterMirrorsBufferedLinesToStreams(): void
    {
        $stdout = fopen('php://memory', 'w+');
        $stderr = fopen('php://memory', 'w+');
        self::assertIsResource($stdout);
        self::assertIsResource($stderr);

        try {
            $writer = new ConsoleWriter($stdout, $stderr);
            $console = new Console($writer);
            $console->line('first');
            $console->line('second');
            $console->errorLine('ERROR reason');

            rewind($stdout);
            rewind($stderr);
            self::assertSame("first\nsecond\n", $writer->stdout());
            self::assertSame("ERROR reason\n", $writer->stderr());
            self::assertSame($writer->stdout(), stream_get_contents($stdout));
            self::assertSame($writer->stderr(), stream_get_contents($stderr));
        } finally {
            fclose($stdout);
            fclose($stderr);
        }
    }

    /**
     * Runs the real check, sync, and init workflows with a writer lacking getters.
     */
    public function testWorkflowsAcceptWriterWithoutBufferGetters(): void
    {
        $root = $this->tempRoot();
        $this->fixture($root, ['tools' => ['phpstan' => ['include' => [], 'exclude' => []]]]);
        /** Records workflow messages without offering buffer inspection methods. */
        $writer = new class () implements ConsoleWriterInterface {
            /** @var list<string> Normal lines received from command execution. */
            public array $lines = [];

            /** @var list<string> Error lines received from command execution. */
            public array $errors = [];

            /**
             * Records a normal line without stream or buffer inspection methods.
             *
             * @param string $line Normal message supplied by the console.
             */
            public function line(string $line): void
            {
                $this->lines[] = $line;
            }

            /**
             * Records an error line without stream or buffer inspection methods.
             *
             * @param string $line Error message supplied by the console.
             */
            public function errorLine(string $line): void
            {
                $this->errors[] = $line;
            }
        };
        $console = new Console($writer);
        $app = Application::default();

        self::assertSame(ExitCode::DRIFT, $app->run(['php-qa-scope', 'check'], $console, $root));
        self::assertSame(ExitCode::SUCCESS, $app->run(['php-qa-scope', 'sync'], $console, $root));
        self::assertSame(ExitCode::SUCCESS, $app->run(['php-qa-scope', 'init'], $console, $root));
        self::assertContains('OUT-OF-SYNC phpstan.neon', $writer->lines);
        self::assertContains('UPDATED phpstan.neon', $writer->lines);
        self::assertContains('OK phpstan.neon', $writer->lines);
        self::assertCount(0, $writer->errors);

        $this->put($root, 'phpstan.neon', "parameters:\n    # php-qa-scope:start\n");
        self::assertSame(ExitCode::ERROR, $app->run(['php-qa-scope', 'check'], $console, $root));
        self::assertCount(1, $writer->errors);
        self::assertStringStartsWith('ERROR phpstan.neon: ', $writer->errors[0]);
    }

    /**
     * Dispatches the supplied facade and reports a thrown command error through it.
     */
    public function testApplicationUsesSameFacadeForDispatchAndCaughtErrors(): void
    {
        $writer = $this->createMock(ConsoleWriterInterface::class);
        $writer->expects(self::never())->method('line');
        $writer->expects(self::once())->method('errorLine')->with('ERROR command failed');
        $console = new Console($writer);
        $command = $this->createMock(Command::class);
        $command->method('name')->willReturn('probe');
        $command->expects(self::once())->method('execute')
            ->with(self::isInstanceOf(Input::class), self::identicalTo($console))
            ->willThrowException(new RuntimeException('command failed'));
        $app = new Application(new CommandRegistry([$command]));

        self::assertSame(ExitCode::ERROR, $app->run(['php-qa-scope', 'probe'], $console, '/repo'));
    }

    /**
     * Keeps separate writers isolated and preserves buffers when explicitly reused.
     */
    public function testCallerOwnsOutputLifetime(): void
    {
        $firstWriter = new ConsoleWriter();
        $secondWriter = new ConsoleWriter();
        $first = new Console($firstWriter);
        $second = new Console($secondWriter);
        $app = Application::default();
        $expected = "ERROR Usage: php-qa-scope <init|sync|check>\n";

        self::assertSame(ExitCode::ERROR, $app->run([], $first, '/repo'));
        self::assertSame('', $secondWriter->stderr());
        self::assertSame(ExitCode::ERROR, $app->run([], $second, '/repo'));
        self::assertSame($expected, $firstWriter->stderr());
        self::assertSame($expected, $secondWriter->stderr());
        self::assertSame(ExitCode::ERROR, $app->run([], $first, '/repo'));
        self::assertSame($expected . $expected, $firstWriter->stderr());
        self::assertSame($expected, $secondWriter->stderr());
        self::assertSame('', $firstWriter->stdout());
        self::assertSame('', $secondWriter->stdout());
    }

    /**
     * Reports missing autoload without needing the unavailable console classes.
     */
    public function testExecutableReportsMissingAutoload(): void
    {
        $root = $this->tempRoot();
        $script = file_get_contents(dirname(__DIR__, 2) . '/bin/php-qa-scope');
        self::assertIsString($script);
        $path = 'isolated/package/bin/php-qa-scope';
        $this->put($root, $path, $script);

        $result = $this->process(['php', $root . '/' . $path], $root);

        self::assertSame(ExitCode::ERROR, $result['code']);
        self::assertSame('', $result['stdout']);
        self::assertSame("ERROR Missing Composer autoload file. Run composer install.\n", $result['stderr']);
    }
}
