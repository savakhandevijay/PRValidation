<?php

declare(strict_types=1);

use PhpCsFixer\Config;
use PhpCsFixer\Finder;

$finder = Finder::create()
    ->in([
        __DIR__ . '/src/www/wss2',
    ])
    ->exclude([
        'vendor',
        'temp',
        'api/runtime',
        'api/views',
        'api/web',
        'grpcadapter',
        'common/tests'
    ])
    ->ignoreDotFiles(true)
    ->ignoreVCS(true);

return (new Config())
    ->setRiskyAllowed(false)
    ->setCacheFile(__DIR__ . '/.php-cs-fixer.cache')
    ->setRules([
        '@PSR12' => true,
        '@PER-CS' => true,
        '@PHP8x4Migration' => true,

        'array_syntax' => [
            'syntax' => 'short',
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

        'no_unused_imports' => true,

        'trailing_comma_in_multiline' => [
            'elements' => [
                'match',
                'arrays',
                'arguments',
                'parameters',
                'array_destructuring'
            ],
        ],
    ])
    ->setFinder($finder);