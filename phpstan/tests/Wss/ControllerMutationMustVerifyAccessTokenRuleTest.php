<?php

declare(strict_types=1);

namespace PHPStanRules\Tests\Wss;

use PHPStanRules\Rules\Wss\ControllerMutationMustVerifyAccessTokenRule;

/**
 * @extends WssRuleTestCase<ControllerMutationMustVerifyAccessTokenRule>
 */
final class ControllerMutationMustVerifyAccessTokenRuleTest extends WssRuleTestCase
{
    protected function getRule(): \PHPStan\Rules\Rule
    {
        return new ControllerMutationMustVerifyAccessTokenRule();
    }

    public function testRule(): void
    {
        $this->analyse([__DIR__ . '/../fixtures/Wss/ControllerMutationMustVerifyAccessTokenRule.php'], [
            ['verifyAccessToken() must be called after request sanitisation.', 11],
        ]);
    }
}
