<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\Tests\Unit;

use GustavoPeixoto\PhpQaScope\Config\EffectiveScope;
use GustavoPeixoto\PhpQaScope\Config\ScopeLoader;
use GustavoPeixoto\PhpQaScope\Tests\TestCase;
use RuntimeException;
use Symfony\Component\Yaml\Yaml;

/**
 * Covers scope configuration loading and effective scope calculation.
 */
final class ScopeLoaderTest extends TestCase
{
    /**
     * Verifies valid configuration is normalized and scoped to listed tools.
     */
    public function testLoadsValidConfigurationAndOnlyListedTools(): void
    {
        $root = $this->tempRoot();
        $this->put($root, 'php-qa-scope.yml', Yaml::dump([
            'include' => ['tests', 'src', 'src'],
            'exclude' => ['**/legacy/**'],
            'tools' => [
                'phpstan' => ['include' => ['bin'], 'exclude' => ['tests/fixtures/**']],
            ],
        ], 5));

        $config = (new ScopeLoader())->load($root . '/php-qa-scope.yml');

        self::assertSame(['phpstan'], $config->managedTools());
        self::assertSame(['src', 'tests'], $config->include);
        self::assertSame(['bin'], $config->tool('phpstan')->include);
    }

    /**
     * Verifies invalid configuration shapes are rejected.
     */
    public function testRejectsInvalidConfigurationShape(): void
    {
        $root = $this->tempRoot();
        $invalidScopes = [
            ['include' => ['src'], 'exclude' => [], 'tools' => ['phpmd' => ['include' => [], 'exclude' => []]]],
            ['include' => ['src'], 'exclude' => [], 'tools' => ['phpstan' => ['include' => []]]],
            ['include' => ['src'], 'exclude' => null, 'tools' => []],
            ['include' => 'src', 'exclude' => [], 'tools' => []],
            ['include' => ['../src'], 'exclude' => [], 'tools' => []],
            ['include' => ['src'], 'exclude' => [], 'tools' => ['phpstan' => null]],
        ];

        foreach ($invalidScopes as $scope) {
            $this->put($root, 'php-qa-scope.yml', Yaml::dump($scope, 5));

            $exception = null;

            try {
                (new ScopeLoader())->load($root . '/php-qa-scope.yml');
            } catch (RuntimeException $error) {
                $exception = $error;
            }

            self::assertInstanceOf(RuntimeException::class, $exception, var_export($scope, true));
        }
    }

    /**
     * Verifies local tool scope extends and overrides global scope.
     */
    public function testCalculatesEffectiveScopeWithPrecedence(): void
    {
        $root = $this->tempRoot();
        $this->put($root, 'php-qa-scope.yml', Yaml::dump([
            'include' => ['src', 'src/legacy', 'tests'],
            'exclude' => ['**/legacy/**'],
            'tools' => [
                'phpstan' => ['include' => ['bin'], 'exclude' => ['tests/fixtures/**']],
            ],
        ], 5));

        $config = (new ScopeLoader())->load($root . '/php-qa-scope.yml');
        $scope = (new EffectiveScope())->calculate($config);

        self::assertSame(['bin', 'src', 'tests'], $scope['phpstan']->include);
        self::assertSame(['**/legacy/**', 'tests/fixtures/**'], $scope['phpstan']->exclude);
    }
}
