<?php

declare(strict_types=1);

namespace PHPStanRules\Rules\Wss;

use PhpParser\Node;
use PhpParser\Node\Expr\MethodCall;
use PhpParser\Node\Expr\New_;
use PhpParser\Node\Expr\StaticCall;
use PhpParser\Node\Name;
use PhpParser\Node\Identifier;
use PHPStan\Analyser\Scope;
use PHPStan\Rules\Rule;
use PHPStan\Rules\RuleErrorBuilder;

/**
 * WSS005: WssAppsetting must be used from common/lib, not models/components/controllers.
 *
 * @implements Rule<Node>
 */
final class AppsettingUsageRule implements Rule
{
    public function getNodeType(): string
    {
        return Node::class;
    }

    /**
     * @param Node $node
     * @return list<\PHPStan\Rules\RuleError>
     */
    public function processNode(Node $node, Scope $scope): array
    {
        if ($this->isAllowedLocation($scope->getFile())) {
            return [];
        }

        $className = $this->getReferencedClassName($node, $scope);

        if ($className !== null && str_ends_with(strtolower($className), 'wssappsetting')) {
            return [
                RuleErrorBuilder::message(
                    'WSS005 Appsettings must be accessed from the common/lib layer, not models/components/controllers.'
                )->identifier('wss005.appsettingLocation')->line($node->getStartLine())->build(),
            ];
        }

        if ($node instanceof MethodCall && $node->name instanceof Identifier) {
            $method = strtolower($node->name->toString());

            if (in_array($method, ['getappsetting', 'getappsettings', 'appsetting', 'appsettings'], true)) {
                return [
                    RuleErrorBuilder::message(
                        'WSS005 Appsettings must be accessed from the common/lib layer, not models/components/controllers.'
                    )->identifier('wss005.appsettingLocation')->line($node->getStartLine())->build(),
                ];
            }
        }

        return [];
    }

    private function isAllowedLocation(string $file): bool
    {
        $normalized = str_replace('\\', '/', $file);

        return str_contains($normalized, '/common/lib/');
    }

    private function getReferencedClassName(Node $node, Scope $scope): ?string
    {
        if ($node instanceof New_ || $node instanceof StaticCall) {
            if ($node->class instanceof Name) {
                return $scope->resolveName($node->class);
            }
        }

        return null;
    }
}
