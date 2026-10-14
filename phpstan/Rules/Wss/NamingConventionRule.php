<?php

declare(strict_types=1);

namespace PHPStanRules\Rules\Wss;

use PhpParser\Node;
use PhpParser\Node\Identifier;
use PhpParser\Node\Stmt\Class_;
use PhpParser\Node\Stmt\ClassConst;
use PhpParser\Node\Stmt\ClassMethod;
use PhpParser\Node\Stmt\Property;
use PHPStan\Analyser\Scope;
use PHPStan\Rules\Rule;
use PHPStan\Rules\RuleErrorBuilder;

/**
 * WSS007: enforce WSS naming conventions that are meaningful at AST level.
 *
 * @implements Rule<Node>
 */
final class NamingConventionRule implements Rule
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
        if ($node instanceof Class_) {
            return $this->checkClass($node, $scope);
        }

        if ($node instanceof ClassMethod) {
            return $this->checkMethod($node, $scope);
        }

        if ($node instanceof Property) {
            return $this->checkProperty($node);
        }

        if ($node instanceof ClassConst) {
            return $this->checkConstants($node);
        }

        return [];
    }

    /**
     * @return list<\PHPStan\Rules\RuleError>
     */
    private function checkClass(Class_ $node, Scope $scope): array
    {
        if ($node->name === null) {
            return [];
        }

        $name = $node->name->toString();
        $errors = [];

        if (!preg_match('/^[A-Z][A-Za-z0-9]*$/', $name)) {
            $errors[] = $this->error('wss007.className', 'WSS007 Class names must use PascalCase.', $node);
        }

        $fileName = pathinfo($scope->getFile(), PATHINFO_FILENAME);

        if ($fileName !== '' && $name !== $fileName && !$this->isGeneratedOrAnonymousContext($scope->getFile())) {
            $errors[] = $this->error(
                'wss007.classFileName',
                sprintf('WSS007 Class "%s" should match its PHP filename "%s.php".', $name, $fileName),
                $node
            );
        }

        return $errors;
    }

    /**
     * @return list<\PHPStan\Rules\RuleError>
     */
    private function checkMethod(ClassMethod $node, Scope $scope): array
    {
        if (!$node->name instanceof Identifier) {
            return [];
        }

        $name = $node->name->toString();
        $errors = [];

        if ($node->isPrivate() || $node->isProtected()) {
            if (!str_starts_with($name, '_') || !preg_match('/^_[a-z][A-Za-z0-9]*$/', $name)) {
                $errors[] = $this->error(
                    'wss007.privateMethod',
                    'WSS007 Private/protected methods must start with "_" followed by camelCase.',
                    $node
                );
            }
        } elseif ($this->isControllerAction($scope, $name)) {
            if (!preg_match('/^action[A-Z][A-Za-z0-9]*$/', $name)) {
                $errors[] = $this->error(
                    'wss007.controllerAction',
                    'WSS007 Yii controller actions must use the actionXxx naming convention.',
                    $node
                );
            }
        } elseif (!preg_match('/^[a-z][A-Za-z0-9]*$/', $name)) {
            $errors[] = $this->error(
                'wss007.methodName',
                'WSS007 Method names must use camelCase.',
                $node
            );
        }

        return $errors;
    }

    /**
     * @return list<\PHPStan\Rules\RuleError>
     */
    private function checkProperty(Property $node): array
    {
        $errors = [];

        if (!$node->isPrivate() && !$node->isProtected()) {
            return [];
        }

        foreach ($node->props as $property) {
            $name = $property->name->toString();

            if (!str_starts_with($name, '__') || !preg_match('/^__[a-z][A-Za-z0-9]*$/', $name)) {
                $errors[] = $this->error(
                    'wss007.propertyName',
                    'WSS007 Private/protected properties must start with "__" followed by camelCase.',
                    $node
                );
            }
        }

        return $errors;
    }

    /**
     * @return list<\PHPStan\Rules\RuleError>
     */
    private function checkConstants(ClassConst $node): array
    {
        $errors = [];

        foreach ($node->consts as $constant) {
            $name = $constant->name->toString();

            if (!preg_match('/^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$/', $name)) {
                $errors[] = $this->error(
                    'wss007.constantName',
                    'WSS007 Constants must use UPPER_CASE_WITH_UNDERSCORES.',
                    $node
                );
            }
        }

        return $errors;
    }

    private function isControllerAction(Scope $scope, string $name): bool
    {
        $class = $scope->getClassReflection();

        return $class !== null
            && (
                $class->getName() === 'common\\components\\WssController'
                || $class->isSubclassOf('common\\components\\WssController')
            )
            && str_starts_with($name, 'action');
    }

    private function isGeneratedOrAnonymousContext(string $file): bool
    {
        return str_contains(str_replace('\\', '/', $file), '/grpcadapter/');
    }

    private function error(string $identifier, string $message, Node $node): \PHPStan\Rules\RuleError
    {
        return RuleErrorBuilder::message($message)
            ->identifier($identifier)
            ->line($node->getStartLine())
            ->build();
    }
}
