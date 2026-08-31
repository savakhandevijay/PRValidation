<?php

declare(strict_types=1);

namespace PHPStanRules\Rules\Yii2;

use PhpParser\Node;
use PhpParser\Node\Expr\StaticCall;
use PHPStan\Analyser\Scope;
use PHPStan\Rules\Rule;
use PHPStan\Rules\RuleErrorBuilder;
use PHPStan\Type\ObjectType;

/**
 * Prevent direct Yii2 ActiveRecord access from Controllers.
 *
 * @implements Rule<StaticCall>
 */
final class NoActiveRecordInControllerRule implements Rule
{
    private const CONTROLLER_SUFFIX = 'Controller';

    private const ACTIVE_RECORD_CLASS = 'yii\db\ActiveRecord';

    private const FORBIDDEN_METHODS = [
        'find',
        'findOne',
        'findAll',
    ];


    public function getNodeType(): string
    {
        // return StaticCall::class;
        return \PhpParser\Node::class;

    }

    public function processNode(Node $node, Scope $scope): array
    {
        if (!$node instanceof StaticCall) {
            return [];
        }

        $classReflection = $scope->getClassReflection();

        if ($classReflection === null) {
            return [];
        }

        /*
         * We only care about Controller classes.
         *
         * Example:
         * ProductController     -> continue
         * ProductService        -> ignore
         * ProductRepository     -> ignore
         */
        if (!str_ends_with(
            $classReflection->getName(),
            self::CONTROLLER_SUFFIX
        )) {
            return [];
        }

        /*
         * We only care about static method calls.
         *
         * Product::find()
         * Order::find()
         */
        if (!$node->class instanceof Node\Name) {
            return [];
        }
        
        if (!$node->name instanceof Node\Identifier) {
            return [];
        }

        $method = $node->name->toString();

        if (!in_array($method, self::FORBIDDEN_METHODS, true)) {
            return [];
        }

        /*
         * For now, report the static call itself.
         * This proves our AST handling is correct without
         * incorrectly using Scope::getType() on Node\Name.
         */
        return [
            RuleErrorBuilder::message(
                sprintf(
                    'Static ActiveRecord query candidate detected: %s::%s()',
                    $node->class->toString(),
                    $method
                )
            )
                ->identifier('yii2.noActiveRecordInController')
                ->build(),
        ];
    }
}