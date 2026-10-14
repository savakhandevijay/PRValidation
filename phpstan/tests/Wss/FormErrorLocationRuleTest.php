<?php

declare(strict_types=1);

namespace PHPStanRules\Tests\Wss;

use PHPStanRules\Rules\Wss\FormErrorLocationRule;

/**
 * @extends WssRuleTestCase<FormErrorLocationRule>
 */
final class FormErrorLocationRuleTest extends WssRuleTestCase
{
    protected function getRule(): \PHPStan\Rules\Rule
    {
        return new FormErrorLocationRule();
    }

    public function testRule(): void
    {
        $this->analyse([__DIR__ . '/../fixtures/Wss/FormErrorLocationRule.php'], [
            ['__formError() may only be used from the common/lib layer.', 9],
        ]);
    }
}
