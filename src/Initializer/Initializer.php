<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Initializer;

use GustavoPeixoto\PhpQaScope\Cli\Output;
use GustavoPeixoto\PhpQaScope\Scope\EffectiveScope;
use GustavoPeixoto\PhpQaScope\Scope\ScopeLoader;
use GustavoPeixoto\PhpQaScope\Synchronizer\Synchronizer;
use GustavoPeixoto\PhpQaScope\Target\TargetRegistry;
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
     * @param TargetInitializer $markers Validation or persisted insertion of empty marker pairs.
     * @param ScopeInitializer $creator Generator and create-only writer for absent YAML.
     * @param TargetRegistry $targets Registry used for target error filenames.
     * @param ScopeLoader $loader Validator for existing and generated scope YAML.
     * @param EffectiveScope $scopes Calculator for each listed tool's scope.
     */
    public function __construct(
        private readonly Synchronizer $synchronizer,
        private readonly TargetInitializer $markers,
        private readonly ScopeInitializer $creator = new ScopeInitializer(),
        private readonly TargetRegistry $targets = new TargetRegistry(),
        private readonly ScopeLoader $loader = new ScopeLoader(),
        private readonly EffectiveScope $scopes = new EffectiveScope(),
    ) {
    }

    /**
     * Inserts empty marker pairs before synchronizing eligible targets.
     *
     * @param string $root Project root containing scope and native configuration files.
     * @param Output $output Destination for per-target statuses and errors.
     * @return InitializerResult Aggregate errors and successful native writes from both phases.
     */
    public function initialize(string $root, Output $output): InitializerResult
    {
        $file = $root . '/php-qa-scope.yml';
        $tools = $this->targets->discover($root);
        $this->creator->create($root, $tools);
        $scopes = $this->scopes->calculate($this->loader->load($file));
        $eligible = [];
        $changed = false;
        $hasErrors = false;

        foreach ($scopes as $tool => $scope) {
            $file = $this->targets->get($tool)->path;

            try {
                if ($this->markers->insert($root, $tool)) {
                    $changed = true;
                }
                $eligible[$tool] = $scope;
            } catch (Throwable $error) {
                $reason = $error->getMessage();
                if (str_starts_with($reason, "$file: ")) {
                    $reason = substr($reason, strlen($file) + 2);
                }
                $output->errorLine("ERROR $file: $reason");
                $hasErrors = true;
            }
        }

        $result = $this->synchronizer->synchronize($root, $eligible, $output);

        return new InitializerResult(
            $hasErrors || $result->hasErrors,
            $changed || $result->changed,
        );
    }
}
