<?php

declare(strict_types=1);

// php-qa-scope:start
$finder = Symfony\Component\Finder\Finder::create()
    ->files()
    ->name('/\.php$/')
    ->ignoreDotFiles(true)
    ->ignoreVCS(false)
    ->in([
        __DIR__ . '/bin',
        __DIR__ . '/src',
        __DIR__ . '/tests',
    ]);
$finder = new CallbackFilterIterator(
    $finder->getIterator(),
    static function (SplFileInfo $file): bool {
        $path = substr(str_replace('\\', '/', $file->getPathname()), strlen(__DIR__) + 1);

        return preg_match('~^(?:php\\-cs\\-fixer\\.dist\\.php$)~D', $path) !== 1;
    },
);

// php-qa-scope:end

$config = new PhpCsFixer\Config();

return $config
    ->setCacheFile(__DIR__ . '/tmp/cs-fixer/.php-cs-fixer.cache')
    ->setRiskyAllowed(false)
    ->setRules([
        '@PSR12' => true,

        'array_syntax' => [
            'syntax' => 'short',
        ],

        'line_ending' => true,
        'encoding' => true,
        'no_trailing_whitespace' => true,
        'no_whitespace_in_blank_line' => true,
        'single_blank_line_at_eof' => true,
        // already aligned with EmptyComment
        'no_empty_comment' => true,
        'no_empty_phpdoc' => true,

        // helps with docblock spacing/shape
        'phpdoc_trim' => true,
        'phpdoc_indent' => true,
        'phpdoc_single_line_var_spacing' => true,
        'phpdoc_summary' => false,
        // annotations and ordering (partially related)
        'phpdoc_order' => [
            'order' => [
                'param',
                'return',
                'throws',
            ],
        ],
        'phpdoc_tag_type' => true,

        // removes truly useless comments/docblocks in some scenarios
        'no_superfluous_phpdoc_tags' => true,

        'binary_operator_spaces' => [
            'default' => 'single_space',
        ],

        'blank_line_before_statement' => [
            'statements' => [
                'return',
                'throw',
                'try',
            ],
        ],

        'concat_space' => [
            'spacing' => 'one',
        ],

        'method_chaining_indentation' => true,

        'no_extra_blank_lines' => true,

        'no_unused_imports' => true,

        'ordered_imports' => [
            'sort_algorithm' => 'alpha',
        ],

        'single_quote' => true,

        'multiline_whitespace_before_semicolons' => ['strategy' => 'new_line_for_chained_calls'],

        'trailing_comma_in_multiline' => [
            // Keep arrays out to avoid conflict with PHPCS Squiz.Arrays.ArrayDeclaration.NoCommaAfterLast.
            'elements' => [
                'arguments',
                'parameters',
                'match',
            ],
        ],

        'method_chaining_indentation' => true,
        'class_attributes_separation' => [
            'elements' => [
                'method' => 'one',
            ],
        ],
        'statement_indentation' => true,
    ])
    ->setFinder($finder);
