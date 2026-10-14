<?php

final class SqlExample
{
    public function bad(int $id): void
    {
        $db = \Yii::$app->repDb;
        $db->createCommand('SELECT * FROM orders WHERE id = ' . $id)->queryAll();
        $db->createCommand("SELECT * FROM orders WHERE id = {$id}")->queryAll();
    }

    public function good(int $id): void
    {
        $db = \Yii::$app->repDb;
        $db->createCommand('SELECT * FROM orders WHERE id = :id')
            ->bindValue(':id', $id)
            ->queryOne();
    }
}
