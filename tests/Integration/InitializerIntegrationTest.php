<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Integration;

use GustavoPeixoto\PhpQaScope\Cli\Output;
use GustavoPeixoto\PhpQaScope\Scope\ToolScope;
use GustavoPeixoto\PhpQaScope\Initializer\Initializer;
use GustavoPeixoto\PhpQaScope\Target\TargetInitializer;
use GustavoPeixoto\PhpQaScope\InsertionLocator\InsertionLocatorRegistry;
use GustavoPeixoto\PhpQaScope\Renderer\Renderer;
use GustavoPeixoto\PhpQaScope\Renderer\RendererRegistry;
use GustavoPeixoto\PhpQaScope\Target\TargetWriter;
use GustavoPeixoto\PhpQaScope\Synchronizer\Synchronizer;
use GustavoPeixoto\PhpQaScope\Target\TargetInspector;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use RuntimeException;

/**
 * Verifies initialization results independently of CLI warnings and exit codes.
 */
final class InitializerIntegrationTest extends TestCase
{
    /**
     * Reports native writes on setup and preserves files on an unchanged retry.
     */
    public function testSuccessfulSetupAndUnchangedRetry(): void
    {
        $root = $this->tempRoot();
        $this->put($root, 'phpstan.neon', "parameters:\n    level: 6\n");
        $initializer = new Initializer(
            new Synchronizer(TargetInspector::default(), new TargetWriter()),
            new TargetInitializer(InsertionLocatorRegistry::default()),
        );
        $output = new Output();

        $result = $initializer->initialize($root, $output);

        self::assertFalse($result->hasErrors);
        self::assertTrue($result->changed);
        self::assertStringContainsString('UPDATED phpstan.neon', $output->stdout());
        self::assertSame('', $output->stderr());
        $before = file_get_contents($root . '/phpstan.neon');
        $inode = fileinode($root . '/phpstan.neon');
        $retryOutput = new Output();

        $retry = $initializer->initialize($root, $retryOutput);

        self::assertFalse($retry->hasErrors);
        self::assertFalse($retry->changed);
        self::assertSame($before, file_get_contents($root . '/phpstan.neon'));
        clearstatcache(true, $root . '/phpstan.neon');
        self::assertSame($inode, fileinode($root . '/phpstan.neon'));
        self::assertStringContainsString('OK phpstan.neon', $retryOutput->stdout());
        self::assertSame('', $retryOutput->stderr());
    }

    /**
     * Retains successful marker writes in the result when synchronization fails.
     */
    public function testMarkerChangesAreReportedAfterSynchronizationFailure(): void
    {
        $root = $this->tempRoot();
        $this->put($root, 'phpstan.neon', "parameters:\n    level: 6\n");
        $failure = new class () implements Renderer {
            /**
             * Simulates a rendering failure after marker insertion has succeeded.
             *
             * @param ToolScope $scope Effective scope provided by the synchronizer.
             * @return string Fragment produced by a successful renderer.
             */
            public function render(ToolScope $scope): string
            {
                throw new RuntimeException('rendering failed');
            }
        };
        $inspector = new TargetInspector(renderers: new RendererRegistry(['phpstan' => $failure]));
        $initializer = new Initializer(
            new Synchronizer($inspector, new TargetWriter()),
            new TargetInitializer(InsertionLocatorRegistry::default()),
        );
        $output = new Output();

        $result = $initializer->initialize($root, $output);

        self::assertTrue($result->hasErrors);
        self::assertTrue($result->changed);
        self::assertStringContainsString('php-qa-scope:start', file_get_contents($root . '/phpstan.neon'));
        self::assertStringContainsString('php-qa-scope:end', file_get_contents($root . '/phpstan.neon'));
        self::assertStringContainsString('ERROR phpstan.neon: rendering failed', $output->stderr());
        self::assertStringNotContainsString('WARNING:', $output->stderr());
    }

    /**
     * Reports marker insertion failures without treating YAML creation as a native change.
     */
    public function testPreparationFailureDoesNotReportNativeChanges(): void
    {
        $root = $this->tempRoot();
        $before = "parameters: { level: 6 }\n";
        $this->put($root, 'phpstan.neon', $before);
        $initializer = new Initializer(
            new Synchronizer(TargetInspector::default(), new TargetWriter()),
            new TargetInitializer(InsertionLocatorRegistry::default()),
        );
        $output = new Output();

        $result = $initializer->initialize($root, $output);

        self::assertTrue($result->hasErrors);
        self::assertFalse($result->changed);
        self::assertFileExists($root . '/php-qa-scope.yml');
        self::assertSame($before, file_get_contents($root . '/phpstan.neon'));
        self::assertSame('', $output->stdout());
        self::assertStringContainsString('ERROR phpstan.neon:', $output->stderr());
    }
}
