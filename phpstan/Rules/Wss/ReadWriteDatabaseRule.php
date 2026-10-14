<?php

declare(strict_types=1);

namespace PHPStanRules\Rules\Wss;

use PhpParser\Node;
use PhpParser\Node\Expr\MethodCall;
use PhpParser\Node\Expr\PropertyFetch;
use PhpParser\Node\Expr\StaticPropertyFetch;
use PHPStan\Analyser\Scope;
use PHPStan\Rules\Rule;
use PHPStan\Rules\RuleErrorBuilder;

/**
 * WSS004: enforce db for writes and repDb for reads.
 *
 * This rule focuses on the explicit Yii::$app->db / Yii::$app->repDb
 * access pattern documented by WSS.
 *
 * @implements Rule<MethodCall>
 */
final class ReadWriteDatabaseRule implements Rule
{
    private const READ_METHODS = [
        'query',
        'queryall',
        'queryone',
        'queryscalar',
        'querycolumn',
        'querybatch',
        'all',
        'one',
        'scalar',
    ];

    private const WRITE_METHODS = [
        'execute',
        'insert',
        'update',
        'delete',
        'upsert',
        'batchinsert',
    ];

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
        if (!$node->name instanceof Node\Identifier) {
            return [];
        }

        $method = strtolower($node->name->toString());
        $connection = $this->findConnectionName($node);

        if ($connection === null) {
            return [];
        }

        if (in_array($method, self::READ_METHODS, true) && $connection === 'db') {
            return [
                RuleErrorBuilder::message(
                    'WSS004 Read operations must use Yii::$app->repDb, not Yii::$app->db.'
                )->identifier('wss004.readWriteSplit')->line($node->getStartLine())->build(),
            ];
        }

        if (in_array($method, self::WRITE_METHODS, true) && $connection === 'repDb') {
            return [
                RuleErrorBuilder::message(
                    'WSS004 Write operations must use Yii::$app->db, not Yii::$app->repDb.'
                )->identifier('wss004.readWriteSplit')->line($node->getStartLine())->build(),
            ];
        }

        return [];
    }

    private function findConnectionName(MethodCall $node): ?string
    {
        $receiver = $node->var;

        if (!$receiver instanceof Expr) {
            return null;
        }

        // queryAll/queryOne/... directly on Yii::$app->db or Yii::$app->repDb.
        if ($receiver instanceof PropertyFetch && $receiver->name instanceof Node\Identifier) {
            $property = $receiver->name->toString();

            if (!in_array($property, ['db', 'repDb'], true)) {
                return null;
            }

            if ($this->isYiiAppFetch($receiver->var)) {
                return $property;
            }

            return null;
        }

        // createCommand(...)->queryAll(), where createCommand receiver is Yii::$app->db.
        if ($receiver instanceof MethodCall) {
            if (!$receiver->name instanceof Node\Identifier || strtolower($receiver->name->toString()) !== 'createcommand') {
                return null;
            }

            $db = $receiver->var;

            if ($db instanceof PropertyFetch && $db->name instanceof Node\Identifier) {
                $property = $db->name->toString();

                if (in_array($property, ['db', 'repDb'], true) && $this->isYiiAppFetch($db->var)) {
                    return $property;
                }
            }
        }

        return null;
    }

    private function isYiiAppFetch(Expr $expression): bool
    {
        return $expression instanceof StaticPropertyFetch
            && $expression->class instanceof Node\Name
            && $expression->class->toString() === 'Yii'
            && $expression->name instanceof Node\Identifier
            && $expression->name->toString() === 'app';
    }
}
