<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Initializer;

use GustavoPeixoto\PhpQaScope\Block\BlockLocator;
use GustavoPeixoto\PhpQaScope\Console\ConsoleWriterInterface;
use GustavoPeixoto\PhpQaScope\InsertionLocator\InsertionLocatorRegistry;
use GustavoPeixoto\PhpQaScope\Renderer\RendererRegistry;
use GustavoPeixoto\PhpQaScope\Scope\ScopeCalculator;
use GustavoPeixoto\PhpQaScope\Scope\ScopeInitializer;
use GustavoPeixoto\PhpQaScope\Scope\ScopeLoader;
use GustavoPeixoto\PhpQaScope\Synchronizer\Synchronizer;
use GustavoPeixoto\PhpQaScope\Target\TargetInitializer;
use GustavoPeixoto\PhpQaScope\Target\TargetInspector;
use GustavoPeixoto\PhpQaScope\Target\TargetRegistry;
use GustavoPeixoto\PhpQaScope\Target\TargetWriter;
use GustavoPeixoto\PhpQaScope\Tool;
use Throwable;

/**
 * Coordinates scope configuration, managed marker insertion, and synchronization.
 */
final class Initializer
{
    /**
     * Creates the initialization workflow with shared synchronization.
     *
     * @param Synchronizer $synchronizer Existing managed-block synchronization workflow.
     * @param TargetInitializer $targetInitializer Validation or persisted insertion of empty marker pairs.
     * @param ScopeInitializer $scopeInitializer Generator and create-only writer for absent YAML.
     * @param TargetRegistry $targets Registry used for target error filenames.
     * @param ScopeLoader $loader Validator for existing and generated scope YAML.
     * @param ScopeCalculator $scopeCalculator Calculator for each listed tool's scope.
     */
    public function __construct(
        private readonly Synchronizer $synchronizer,
        private readonly TargetInitializer $targetInitializer,
        private readonly ScopeInitializer $scopeInitializer,
        private readonly TargetRegistry $targets,
        private readonly ScopeLoader $loader,
        private readonly ScopeCalculator $scopeCalculator,
    ) {
    }

    /**
     * Builds a standalone initialization graph sharing its scope and native-file collaborators.
     *
     * @return self Service configured with built-in collaborators.
     */
    public static function default(): self
    {
        $loader = new ScopeLoader();
        $scopeCalculator = ScopeCalculator::default();
        $targets = TargetRegistry::default();
        $blockLocator = new BlockLocator();
        $writer = new TargetWriter();
        $inspector = new TargetInspector(
            $loader,
            $scopeCalculator,
            RendererRegistry::default(),
            $targets,
            $blockLocator,
        );

        return new self(
            new Synchronizer($inspector, $writer),
            new TargetInitializer(InsertionLocatorRegistry::default(), $targets, $blockLocator, $writer),
            new ScopeInitializer(),
            $targets,
            $loader,
            $scopeCalculator,
        );
    }

    /**
     * Inserts empty marker pairs before synchronizing eligible targets.
     *
     * @param string $root Project root containing scope and native configuration files.
     * @param ConsoleWriterInterface $console Destination for per-target statuses and errors.
     * @return InitializerResult Aggregate errors and successful native writes from both phases.
     */
    public function initialize(string $root, ConsoleWriterInterface $console): InitializerResult
    {
        $file = $root . '/php-qa-scope.yml';
        $tools = $this->targets->discover($root);
        $this->scopeInitializer->create($root, $tools);
        $scopes = $this->scopeCalculator->calculate($this->loader->load($file));
        $eligible = [];
        $changed = false;
        $hasErrors = false;

        foreach ($scopes as $toolName => $scope) {
            $tool = Tool::from($toolName);
            $file = $this->targets->get($tool)->path;

            try {
                if ($this->targetInitializer->insert($root, $tool)) {
                    $changed = true;
                }
                $eligible[$toolName] = $scope;
            } catch (Throwable $error) {
                $reason = $error->getMessage();
                if (str_starts_with($reason, "$file: ")) {
                    $reason = substr($reason, strlen($file) + 2);
                }
                $console->errorLine("ERROR $file: $reason");
                $hasErrors = true;
            }
        }

        $result = $this->synchronizer->synchronize($root, $eligible, $console);

        return new InitializerResult(
            $hasErrors || $result->hasErrors,
            $changed || $result->changed,
        );
    }
}
