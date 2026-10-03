<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit\Composition;

use GustavoPeixoto\PhpQaScope\Application;
use GustavoPeixoto\PhpQaScope\Cli\Input;
use GustavoPeixoto\PhpQaScope\Command\Command;
use GustavoPeixoto\PhpQaScope\Command\CommandRegistry;
use GustavoPeixoto\PhpQaScope\Console\Console;
use GustavoPeixoto\PhpQaScope\Console\ConsoleWriter;
use GustavoPeixoto\PhpQaScope\Console\ConsoleWriterInterface;
use GustavoPeixoto\PhpQaScope\Initializer\Initializer;
use GustavoPeixoto\PhpQaScope\Target\TargetInitializer;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use GustavoPeixoto\PhpQaScope\Tool;
use ReflectionProperty;

/**
 * Covers usable standalone factories and application-local collaborator sharing.
 */
final class CompositionTest extends TestCase
{
    /**
     * Uses standalone defaults without caller dependency setup and safely retries.
     */
    public function testStandaloneInitializationFactories(): void
    {
        $root = $this->tempRoot();
        $this->put($root, 'phpstan.neon', "parameters:\n    level: 6\n");
        self::assertTrue(TargetInitializer::default()->insert($root, Tool::Phpstan));
        $initializer = Initializer::default();
        $result = $initializer->initialize($root, new ConsoleWriter());
        self::assertFalse($result->hasErrors);
        self::assertTrue($result->changed);
        $retry = $initializer->initialize($root, new ConsoleWriter());
        self::assertFalse($retry->hasErrors);
        self::assertFalse($retry->changed);
    }

    /**
     * Shares scope, target, marker, and writer collaborators within one application.
     */
    public function testApplicationSharesItsGraph(): void
    {
        $app = Application::default();
        $initializer = $this->collaborator($this->command($app, 'init'), 'initializer');
        $targetInitializer = $this->collaborator($initializer, 'targetInitializer');
        $synchronizer = $this->collaborator($initializer, 'synchronizer');
        $inspector = $this->collaborator($synchronizer, 'inspector');

        self::assertSame($synchronizer, $this->collaborator($this->command($app, 'sync'), 'synchronizer'));
        self::assertSame($inspector, $this->collaborator($this->command($app, 'sync'), 'inspector'));
        self::assertSame($inspector, $this->collaborator($this->command($app, 'check'), 'inspector'));
        self::assertSame($this->collaborator($initializer, 'loader'), $this->collaborator($inspector, 'loader'));
        self::assertSame(
            $this->collaborator($initializer, 'scopeCalculator'),
            $this->collaborator($inspector, 'scopeCalculator'),
        );
        self::assertSame($this->collaborator($initializer, 'targets'), $this->collaborator($inspector, 'targets'));
        self::assertSame(
            $this->collaborator($targetInitializer, 'targets'),
            $this->collaborator($inspector, 'targets'),
        );
        self::assertSame(
            $this->collaborator($targetInitializer, 'blockLocator'),
            $this->collaborator($inspector, 'blockLocator'),
        );
        self::assertSame(
            $this->collaborator($targetInitializer, 'writer'),
            $this->collaborator($synchronizer, 'writer'),
        );

        $otherInspector = $this->collaborator($this->command(Application::default(), 'check'), 'inspector');
        self::assertNotSame($inspector, $otherInspector);
        foreach (['loader', 'scopeCalculator', 'renderers', 'targets', 'blockLocator'] as $name) {
            self::assertNotSame($this->collaborator($inspector, $name), $this->collaborator($otherInspector, $name));
        }
    }

    /**
     * Reads a private collaborator to check the composition lifetime contract.
     *
     * @param object $owner Object holding the collaborator.
     * @param string $name Collaborator property to inspect.
     * @return object Collaborator supplied to the owner.
     */
    private function collaborator(object $owner, string $name): object
    {
        $value = (new ReflectionProperty($owner, $name))->getValue($owner);
        self::assertIsObject($value);

        return $value;
    }

    /**
     * Resolves a command from an application's supplied command graph.
     *
     * @param Application $app Application whose graph is inspected.
     * @param string $name Registered command name.
     * @return Command Supplied command instance.
     */
    private function command(Application $app, string $name): Command
    {
        $registry = $this->collaborator($app, 'commands');
        self::assertInstanceOf(CommandRegistry::class, $registry);

        return $registry->get($name);
    }

    /**
     * Dispatches supplied commands without contaminating another application's registry.
     */
    public function testCustomApplicationsRemainIndependent(): void
    {
        $first = new Application(new CommandRegistry([$this->customCommand(0)]));
        $second = new Application(new CommandRegistry([$this->customCommand(1)]));

        self::assertSame(0, $first->run(['php-qa-scope', 'probe'], new Console(new ConsoleWriter()), '/repo'));
        self::assertSame(1, $second->run(['php-qa-scope', 'probe'], new Console(new ConsoleWriter()), '/repo'));
        self::assertSame(0, $first->run(['php-qa-scope', 'probe'], new Console(new ConsoleWriter()), '/repo'));
    }

    /**
     * Creates a custom command with a recognizable execution result.
     *
     * @param int $code Exit code returned by the supplied command.
     * @return Command Command used to check registry isolation.
     */
    private function customCommand(int $code): Command
    {
        return new class ($code) implements Command {
            /**
             * Captures the result distinguishing independently supplied commands.
             *
             * @param int $code Exit code returned by execution.
             */
            public function __construct(private readonly int $code)
            {
            }

            /**
             * Returns the shared name used to test independent resolution.
             *
             * @return string Registered command name.
             */
            public function name(): string
            {
                return 'probe';
            }

            /**
             * Returns this command's supplied result without filesystem access.
             *
             * @param Input $input Parsed input supplied by the application.
             * @param ConsoleWriterInterface $console Console destination supplied by the application.
             * @return int Recognizable execution result.
             */
            public function execute(Input $input, ConsoleWriterInterface $console): int
            {
                return $this->code;
            }
        };
    }
}
