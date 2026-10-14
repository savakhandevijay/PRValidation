<?php

namespace app\controllers;

use common\components\WssController;

final class OrderController extends WssController
{
    public function actionBad(): array
    {
        if ($this->request->isPost) {
            $this->verifyAccessToken();
            $this->sanitizeInput();
        }

        return [];
    }

    public function actionGood(): array
    {
        if ($this->request->isPost) {
            $this->sanitizeInput();
            $this->verifyAccessToken();
        }

        return [];
    }
}
