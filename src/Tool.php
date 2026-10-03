<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope;

/**
 * Identifies the supported native QA tools by their external configuration keys.
 */
enum Tool: string
{
    case Phpcs = 'phpcs';
    case Phpstan = 'phpstan';
    case PhpCsFixer = 'php-cs-fixer';
}
