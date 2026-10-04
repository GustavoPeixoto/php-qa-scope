<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\InsertionLocator;

use ParseError;
use RuntimeException;

/**
 * Finds a conventional PHP preamble boundary without executing configuration.
 */
final class PhpCsFixerInsertionLocator implements InsertionLocator
{
    /**
     * Locates an insertion point after the opening tag and leading declarations.
     *
     * @param string $contents Original PHP configuration bytes.
     *
     * @return int Offset before existing executable configuration code.
     */
    public function locate(string $contents): int
    {
        try {
            $tokens = token_get_all($contents, TOKEN_PARSE);
        } catch (ParseError $error) {
            throw new RuntimeException('could not parse a conventional PHP configuration.', 0, $error);
        }
        if (!isset($tokens[0]) || !is_array($tokens[0]) || $tokens[0][0] !== T_OPEN_TAG) {
            throw new RuntimeException('could not recognize a conventional PHP opening tag.');
        }

        $this->assertSupportedLayout($tokens);

        return $this->preambleEnd($tokens, strlen($tokens[0][1]));
    }

    /**
     * Rejects namespaces and mixed layouts that require manual marker placement.
     *
     * @param list<array{0: int, 1: string, 2: int}|string> $tokens Tokens from the parsed PHP file.
     */
    private function assertSupportedLayout(array $tokens): void
    {
        $openingTags = 0;
        foreach ($tokens as $token) {
            if (!is_array($token)) {
                continue;
            }
            if ($token[0] === T_OPEN_TAG) {
                ++$openingTags;
            }
            if (in_array($token[0], [T_NAMESPACE, T_INLINE_HTML, T_OPEN_TAG_WITH_ECHO, T_CLOSE_TAG], true)) {
                throw new RuntimeException('namespace or mixed PHP layouts require manual marker placement.');
            }
        }
        if ($openingTags !== 1) {
            throw new RuntimeException('multiple PHP opening tags require manual marker placement.');
        }
    }

    /**
     * Finds the byte offset after the opening tag and leading declarations.
     *
     * @param list<array{0: int, 1: string, 2: int}|string> $tokens Tokens from the validated PHP file.
     * @param int $position Byte offset immediately after the opening tag.
     *
     * @return int Offset before existing executable configuration code.
     */
    private function preambleEnd(array $tokens, int $position): int
    {
        $anchor = $position;
        $index = 1;
        while (isset($tokens[$index])) {
            $token = $tokens[$index];
            if ($this->isTrivia($token)) {
                $position += strlen(is_array($token) ? $token[1] : $token);
                ++$index;

                continue;
            }
            if (!is_array($token) || $token[0] !== T_DECLARE) {
                break;
            }

            $end = $this->declarationEnd($tokens, $index);
            while ($index <= $end) {
                $part = $tokens[$index];
                $position += strlen(is_array($part) ? $part[1] : $part);
                ++$index;
            }
            $anchor = $position;
        }

        return $anchor;
    }

    /**
     * Recognizes whitespace and comments that do not execute configuration code.
     *
     * @param array{0: int, 1: string, 2: int}|string $token Token from PHP's lexer.
     *
     * @return bool Whether this token belongs to preamble trivia.
     */
    private function isTrivia(array|string $token): bool
    {
        return is_array($token) && in_array($token[0], [T_WHITESPACE, T_COMMENT, T_DOC_COMMENT], true);
    }

    /**
     * Finds the semicolon closing a leading declaration and rejects block form.
     *
     * @param list<array{0: int, 1: string, 2: int}|string> $tokens Tokens from the parsed PHP file.
     * @param int $start Index of the declaration keyword.
     *
     * @return int Index of the declaration's terminating semicolon.
     */
    private function declarationEnd(array $tokens, int $start): int
    {
        $depth = 0;
        $opened = false;
        for ($index = $start + 1; isset($tokens[$index]); ++$index) {
            $token = $tokens[$index];
            if ($this->isTrivia($token)) {
                continue;
            }
            if ($token === '(') {
                ++$depth;
                $opened = true;
            } elseif ($token === ')') {
                --$depth;
            } elseif ($opened && $depth === 0) {
                if ($token === ';') {
                    return $index;
                }

                break;
            }
        }

        throw new RuntimeException('unsupported initial declare layout requires manual marker placement.');
    }
}
