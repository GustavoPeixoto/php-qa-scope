---
id: phpdoc
title: PHPDoc Convention
when: Whenever creating or changing PHP source code in `src/`, `tests/`, or other package PHP files.
---

# PHPDoc Convention

## General Rule

Use PHPDoc to document both intent and static-analysis precision.

Class-like declarations must explain what the type is responsible for. This applies to classes, interfaces, traits, and enums.

Every method and function must have a PHPDoc summary that describes the behavior or contract. Every parameter must be documented with `@param`. Every non-`void` return must be documented with `@return`.

## Descriptions

Write descriptions that explain meaning, not syntax. Avoid repeating the symbol name without adding intent.

Prefer:

```php
/**
 * Builds the default command dispatcher for the package CLI.
 *
 * @return self Dispatcher configured with the built-in commands.
 */
public static function default(): self
{
}
```

Avoid:

```php
/**
 * Default.
 *
 * @return self Self.
 */
public static function default(): self
{
}
```

## Parameters And Returns

Document every parameter with its type, variable name, and purpose. When a method or function returns a non-`void` value, document the returned value with `@return`.

Do not add `@return void` for `void` methods or functions.

Use PHPDoc types to express shapes that native PHP types cannot express, including `list<T>`, `array<TKey, TValue>`, array shapes, resources, and callable signatures.

## Templates

Use `@template` when a class, interface, trait, method, or function models a generic type.

The template must be connected to the documented contract through `@param`, `@return`, `@var`, `@extends`, `@implements`, or `@use`. Do not declare unused templates.

Prefer meaningful template names such as `TValue`, `TKey`, `TCommand`, or `TRenderer`.

```php
/**
 * Stores values by normalized key.
 *
 * @template TValue
 */
final class Registry
{
    /** @var array<string, TValue> Values indexed by normalized key. */
    private array $values = [];
}
```

## Closures And Callables

Whenever a property, parameter, or return value is a closure or callable, document the callable signature.

```php
/**
 * Filters paths with a predicate.
 *
 * @param list<string> $paths Paths to filter.
 * @param callable(string): bool $accepts Predicate that accepts paths to keep.
 * @return list<string> Paths accepted by the predicate.
 */
public function filter(array $paths, callable $accepts): array
{
}
```

```php
/**
 * Builds a path matcher.
 *
 * @return \Closure(string): bool Matcher that returns true when the path is accepted.
 */
public function matcher(): \Closure
{
}
```

```php
/** @var \Closure(string): string Normalizes a path before rendering. */
private \Closure $normalize;
```

Inline closures should use native parameter and return types whenever possible.
