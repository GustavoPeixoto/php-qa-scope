<?php

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

        'cast_spaces' => true,

        'concat_space' => [
            'spacing' => 'one',
        ],

        'declare_strict_types' => true,

        'method_chaining_indentation' => true,

        'no_extra_blank_lines' => true,

        'no_unused_imports' => true,

        'ordered_imports' => [
            'sort_algorithm' => 'alpha',
        ],

        'single_quote' => true,

        'trailing_comma_in_multiline' => [
            'elements' => [
                'arrays',
                'arguments',
                'parameters',
            ],
        ],
    ])
    ->setFinder($finder);
