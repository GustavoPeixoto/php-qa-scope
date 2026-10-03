<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Target;

use GustavoPeixoto\PhpQaScope\Tool;

/**
 * Describes a native QA tool configuration file managed by php-qa-scope.
 */
final readonly class TargetFile
{
    /**
     * Creates a target file definition.
     *
     * @param Tool $tool Managed tool name.
     * @param string $path Target path relative to the project root.
     * @param string $marker Marker format containing one string placeholder for the edge.
     * @param string $indent Required marker indentation.
     */
    public function __construct(
        public Tool $tool,
        public string $path,
        public string $marker,
        public string $indent,
    ) {
    }
}
