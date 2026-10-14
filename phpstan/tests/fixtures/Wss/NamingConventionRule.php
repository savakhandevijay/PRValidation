<?php

final class BadName
{
    private string $badProperty;

    private function badPrivate(): void
    {
    }

    public function goodMethod(): void
    {
    }

    private const bad_constant = 1;
}
