<?php

final class DbExample
{
    public function badRead(): void
    {
        \Yii::$app->db->createCommand('SELECT * FROM orders')->queryAll();
    }

    public function badWrite(): void
    {
        \Yii::$app->repDb->createCommand('DELETE FROM orders WHERE id = :id')->execute();
    }

    public function good(): void
    {
        \Yii::$app->repDb->createCommand('SELECT * FROM orders')->queryAll();
        \Yii::$app->db->createCommand('DELETE FROM orders WHERE id = :id')->execute();
    }
}
