<?php

declare(strict_types=1);

namespace PHPStanRules\Rules\Wss;

use PhpParser\Node;
use PhpParser\Node\Expr\MethodCall;
use PhpParser\Node\Identifier;
use PHPStan\Analyser\Scope;
use PHPStan\Rules\Rule;
use PHPStan\Rules\RuleErrorBuilder;

/**
 * WSS006: __formError() is a lib-layer helper.
 *
 * @implements Rule<MethodCall>
 */
final class FormErrorLocationRule implements Rule
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
        if (!$node->name instanceof Identifier || $node->name->toString() !== '__formError') {
            return [];
        }

        $file = str_replace('\\', '/', $scope->getFile());

        if (str_contains($file, '/common/lib/')) {
            return [];
        }

        return [
            RuleErrorBuilder::message(
                '__formError() may only be used from the common/lib layer.'
            )->identifier('wss006.formErrorLocation')->line($node->getStartLine())->build(),
        ];
    }
}
