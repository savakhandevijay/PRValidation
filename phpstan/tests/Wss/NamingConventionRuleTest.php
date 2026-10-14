<?php

declare(strict_types=1);

namespace PHPStanRules\Tests\Wss;

use PHPStanRules\Rules\Wss\NamingConventionRule;

/**
 * @extends WssRuleTestCase<NamingConventionRule>
 */
final class NamingConventionRuleTest extends WssRuleTestCase
{
    protected function getRule(): \PHPStan\Rules\Rule
    {
        return new NamingConventionRule();
    }

    public function testRule(): void
    {
        $this->analyse([__DIR__ . '/../fixtures/Wss/NamingConventionRule.php'], [
            ['Private/protected properties must start with "__" followed by camelCase.', 7],
            ['Private/protected methods must start with "_" followed by camelCase.', 9],
            ['Constants must use UPPER_CASE_WITH_UNDERSCORES.', 19],
        ]);
    }
}
