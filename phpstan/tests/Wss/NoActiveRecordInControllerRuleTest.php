<?php

declare(strict_types=1);

namespace PHPStanRules\Tests\Wss;

use PHPStanRules\Rules\Wss\NoActiveRecordInControllerRule;

/**
 * @extends WssRuleTestCase<NoActiveRecordInControllerRule>
 */
final class NoActiveRecordInControllerRuleTest extends WssRuleTestCase
{
    protected function getRule(): \PHPStan\Rules\Rule
    {
        return new NoActiveRecordInControllerRule();
    }

    public function testRule(): void
    {
        $this->analyse([__DIR__ . '/../fixtures/Wss/NoActiveRecordInControllerRule.php'], [
            ['Controllers must not access ActiveRecord directly. Delegate database work to the model/lib layer.', 12],
        ]);
    }
}
