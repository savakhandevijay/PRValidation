<?php

declare(strict_types=1);

namespace PHPStanRules\Tests\Wss;

use PHPStanRules\Rules\Wss\RawSqlMustUseParametersRule;

/**
 * @extends WssRuleTestCase<RawSqlMustUseParametersRule>
 */
final class RawSqlMustUseParametersRuleTest extends WssRuleTestCase
{
    protected function getRule(): \PHPStan\Rules\Rule
    {
        return new RawSqlMustUseParametersRule();
    }

    public function testRule(): void
    {
        $this->analyse([__DIR__ . '/../fixtures/Wss/RawSqlMustUseParametersRule.php'], [
            ['WSS003 Raw SQL must not concatenate or interpolate runtime values. Use named placeholders with bindValue()/bindValues().', 9],
            ['WSS003 Raw SQL must not concatenate or interpolate runtime values. Use named placeholders with bindValue()/bindValues().', 10],
        ]);
    }
}
