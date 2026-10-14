<?php

declare(strict_types=1);

namespace PHPStanRules\Tests\Wss;

use PHPStan\Testing\RuleTestCase;

/**
 * @template T of \PHPStan\Rules\Rule
 * @extends RuleTestCase<T>
 */
abstract class WssRuleTestCase extends RuleTestCase
{
    protected function getAdditionalConfigFiles(): array
    {
        return [
            __DIR__ . '/../../phpstan.test.neon',
        ];
    }
}
