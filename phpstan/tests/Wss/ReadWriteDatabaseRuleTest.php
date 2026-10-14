<?php

declare(strict_types=1);

namespace PHPStanRules\Tests\Wss;

use PHPStanRules\Rules\Wss\ReadWriteDatabaseRule;

/**
 * @extends WssRuleTestCase<ReadWriteDatabaseRule>
 */
final class ReadWriteDatabaseRuleTest extends WssRuleTestCase
{
    protected function getRule(): \PHPStan\Rules\Rule
    {
        return new ReadWriteDatabaseRule();
    }

    public function testRule(): void
    {
        $this->analyse([__DIR__ . '/../fixtures/Wss/ReadWriteDatabaseRule.php'], [
            ['Read operations must use Yii::$app->repDb, not Yii::$app->db.', 7],
            ['Write operations must use Yii::$app->db, not Yii::$app->repDb.', 12],
        ]);
    }
}
