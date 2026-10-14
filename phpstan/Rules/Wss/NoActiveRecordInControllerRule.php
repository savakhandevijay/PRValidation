<?php

declare(strict_types=1);

namespace PHPStanRules\Rules\Wss;

use PhpParser\Node;
use PhpParser\Node\Expr\MethodCall;
use PhpParser\Node\Expr\StaticCall;
use PHPStan\Analyser\Scope;
use PHPStan\Rules\Rule;
use PHPStan\Rules\RuleErrorBuilder;

/**
 * WSS001: controllers must not access ActiveRecord or perform DB work directly.
 *
 * @implements Rule<Node\Expr>
 */
final class NoActiveRecordInControllerRule implements Rule
{
    /**
     * @return class-string<Node\Expr\StaticCall|Node\Expr\MethodCall>
     */
    public function getNodeType(): string
    {
        return Node\Expr::class;
    }

    /**
     * @param Node\Expr $node
     * @return list<\PHPStan\Rules\RuleError>
     */
    public function processNode(Node $node, Scope $scope): array
    {
        if (!$scope->isInClass() || !$this->isWssController($scope)) {
            return [];
        }

        if ($node instanceof StaticCall) {
            $methodName = $node->name instanceof Node\Identifier
                ? $node->name->toString()
                : null;

            if ($methodName === null) {
                return [];
            }

            $className = $node->class instanceof Node\Name
                ? $scope->resolveName($node->class)
                : null;

            if (
                $className !== null
                && (
                    str_ends_with($className, 'ActiveRecord')
                    || $methodName === 'find'
                    || $methodName === 'findOne'
                )
            ) {
                return [$this->error('WSS001', 'Controllers must not access ActiveRecord directly. Delegate database work to the model/lib layer.', $node)];
            }

            return [];
        }

        if (!$node instanceof MethodCall || !$node->name instanceof Node\Identifier) {
            return [];
        }

        $methodName = strtolower($node->name->toString());

        if (
            in_array($methodName, ['save', 'insert', 'update', 'delete', 'deleteall', 'updateall', 'saveall'], true)
            || in_array($methodName, ['createcommand', 'queryall', 'queryone', 'queryscalar', 'querycolumn', 'execute'], true)
        ) {
            return [$this->error('WSS001', 'Controllers must not perform database/ActiveRecord operations directly. Delegate the operation to the model/lib layer.', $node)];
        }

        return [];
    }

    private function isWssController(Scope $scope): bool
    {
        $class = $scope->getClassReflection();

        if ($class === null) {
            return false;
        }

        return $class->getName() === 'common\\components\\WssController'
            || $class->isSubclassOf('common\\components\\WssController');
    }

    private function error(string $identifier, string $message, Node $node): \PHPStan\Rules\RuleError
    {
        return RuleErrorBuilder::message($message)
            ->identifier(strtolower($identifier))
            ->line($node->getStartLine())
            ->build();
    }
}
