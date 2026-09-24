<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Renderer;

use GustavoPeixoto\PhpQaScope\Config\ToolScope;

/**
 * Defines a renderer for one native QA tool configuration block.
 */
interface Renderer
{
    /**
     * Renders a native configuration fragment for a tool scope.
     *
     * @param ToolScope $scope Scope to render.
     * @return string Native configuration fragment for the managed block.
     */
    public function render(ToolScope $scope): string;
}
