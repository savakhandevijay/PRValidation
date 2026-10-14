<?php

declare(strict_types=1);

namespace PHPStanRules\Rules\Wss;

use PhpParser\Node;
use PhpParser\Node\Expr\MethodCall;
use PhpParser\Node\Stmt\ClassMethod;
use PhpParser\NodeFinder;
use PHPStan\Analyser\Scope;
use PHPStan\Rules\Rule;
use PHPStan\Rules\RuleErrorBuilder;

/**
 * WSS002: mutation controller actions must sanitise input and verify the access token.
 *
 * This rule intentionally reports only actions where the AST contains evidence
 * of POST/PUT/DELETE handling. It does not guess HTTP routing metadata.
 *
 * @implements Rule<ClassMethod>
 */
final class ControllerMutationMustVerifyAccessTokenRule implements Rule
{
    public function getNodeType(): string
    {
        return ClassMethod::class;
    }

    /**
     * @param ClassMethod $node
     * @return list<\PHPStan\Rules\RuleError>
     */
    public function processNode(Node $node, Scope $scope): array
    {
        if (!$scope->isInClass() || !$this->isWssController($scope)) {
            return [];
        }

        $name = $node->name->toString();

        if (!str_starts_with($name, 'action') || $node->stmts === null) {
            return [];
        }

        $finder = new NodeFinder();
        $calls = $finder->findInstanceOf($node->stmts, MethodCall::class);

        $hasMutationEvidence = false;
        $verifyLine = null;
        $sanitizeLine = null;

        foreach ($calls as $call) {
            if (!$call->name instanceof Node\Identifier) {
                continue;
            }

            $method = strtolower($call->name->toString());

            if (in_array($method, ['ispost', 'isput', 'isdelete', 'getispost', 'getisput', 'getisdelete'], true)) {
                $hasMutationEvidence = true;
            }

            if ($method === 'getmethod') {
                $hasMutationEvidence = $hasMutationEvidence || $this->hasMutationStringArgument($call);
            }

            if ($method === 'verifyaccesstoken') {
                $verifyLine = $call->getStartLine();
            }

            if ($this->looksLikeSanitizer($method)) {
                $sanitizeLine = $call->getStartLine();
            }
        }

        if (!$hasMutationEvidence) {
            return [];
        }

        $errors = [];

        if ($sanitizeLine === null) {
            $errors[] = RuleErrorBuilder::message(
                'WSS002 Mutation controller actions must sanitise request input before verification.'
            )->identifier('wss002.mutationAuthentication')->line($node->getStartLine())->build();
        }

        if ($verifyLine === null) {
            $errors[] = RuleErrorBuilder::message(
                'WSS002 POST/PUT/DELETE controller actions must call verifyAccessToken().'
            )->identifier('wss002.mutationAuthentication')->line($node->getStartLine())->build();
        } elseif ($sanitizeLine !== null && $verifyLine < $sanitizeLine) {
            $errors[] = RuleErrorBuilder::message(
                'WSS002 verifyAccessToken() must be called after request sanitisation.'
            )->identifier('wss002.mutationAuthentication')->line($verifyLine)->build();
        }

        return $errors;
    }

    private function looksLikeSanitizer(string $method): bool
    {
        return str_contains($method, 'sanitize')
            || str_contains($method, 'sanitise')
            || str_contains($method, 'sanitizeinput')
            || str_contains($method, 'sanitiseinput');
    }

    private function hasMutationStringArgument(MethodCall $call): bool
    {
        foreach ($call->args as $arg) {
            if ($arg->value instanceof Node\Scalar\String_) {
                if (in_array(strtoupper($arg->value->value), ['POST', 'PUT', 'DELETE'], true)) {
                    return true;
                }
            }
        }

        return false;
    }

    private function isWssController(Scope $scope): bool
    {
        $class = $scope->getClassReflection();

        return $class !== null
            && (
                $class->getName() === 'common\\components\\WssController'
                || $class->isSubclassOf('common\\components\\WssController')
            );
    }
}
