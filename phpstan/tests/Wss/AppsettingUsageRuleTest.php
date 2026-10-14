<?php

declare(strict_types=1);

namespace PHPStanRules\Tests\Wss;

use PHPStanRules\Rules\Wss\AppsettingUsageRule;

/**
 * @extends WssRuleTestCase<AppsettingUsageRule>
 */
final class AppsettingUsageRuleTest extends WssRuleTestCase
{
    protected function getRule(): \PHPStan\Rules\Rule
    {
        return new AppsettingUsageRule();
    }

    public function testRule(): void
    {
        $this->analyse([__DIR__ . '/../fixtures/Wss/AppsettingUsageRule.php'], [
            ['Appsettings must be accessed from the common/lib layer, not models/components/controllers.', 10],
        ]);
    }
}
