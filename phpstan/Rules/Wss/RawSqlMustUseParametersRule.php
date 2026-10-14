<?php

declare(strict_types=1);

namespace PHPStanRules\Rules\Wss;

use PhpParser\Node;
use PhpParser\Node\Expr;
use PhpParser\Node\Expr\BinaryOp\Concat;
use PhpParser\Node\Expr\FuncCall;
use PhpParser\Node\Expr\MethodCall;
use PhpParser\Node\Expr\String_;
use PhpParser\Node\Scalar\Encapsed;
use PHPStan\Analyser\Scope;
use PHPStan\Rules\Rule;
use PHPStan\Rules\RuleErrorBuilder;

/**
 * WSS003: dynamic SQL passed to Yii createCommand must use bound parameters.
 *
 * The first iteration deliberately catches direct concatenation/interpolation.
 * It does not attempt whole-program taint/data-flow analysis.
 *
 * @implements Rule<MethodCall>
 */
final class RawSqlMustUseParametersRule implements Rule
{
    public function getNodeType(): string
    {
        return MethodCall::class;
    }

    /**
     * @param MethodCall $node
     * @return list<\PHPStan\Rules\RuleError>
     */
    public function processNode(Node $node, Scope $scope): array
    {
        if (!$node->name instanceof Node\Identifier || strtolower($node->name->toString()) !== 'createcommand') {
            return [];
        }

        $argument = $node->args[0]->value ?? null;

        if (!$argument instanceof Expr) {
            return [];
        }

        if ($this->isUnsafeSqlExpression($argument)) {
            return [
                RuleErrorBuilder::message(
                    'WSS003 Raw SQL must not concatenate or interpolate runtime values. Use named placeholders with bindValue()/bindValues().'
                )->identifier('wss003.rawSqlParameters')->line($node->getStartLine())->build(),
            ];
        }

        return [];
    }

    private function isUnsafeSqlExpression(Expr $expression): bool
    {
        if ($expression instanceof Concat || $expression instanceof Encapsed) {
            return true;
        }

        // A function-generated SQL string is dynamic and cannot be proven safe here.
        if ($expression instanceof FuncCall) {
            return true;
        }

        return false;
    }
}
