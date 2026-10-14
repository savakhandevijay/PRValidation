<?php

namespace app\controllers;

use common\components\WssController;
use common\models\Order;

final class OrderController extends WssController
{
    public function actionBad(): array
    {
        $order = Order::find()->where(['id' => 1])->one();

        return ['error' => false, 'data' => $order];
    }

    public function actionGood(): array
    {
        return $this->lib->getOrder(1);
    }
}
