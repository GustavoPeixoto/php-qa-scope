<?php

declare(strict_types=1);

namespace GustavoPeixoto\PhpQaScope\InsertionLocator;

use RuntimeException;

/**
 * Finds a PHPCS ruleset opening element without interpreting comments as tags.
 */
final class PhpCodeSnifferInsertionLocator implements InsertionLocator
{
    /**
     * Finds the end of the first recognizable non-self-closing ruleset opening tag.
     *
     * @param string $contents Original XML configuration bytes.
     *
     * @return int Offset immediately after the ruleset opening element.
     */
    public function locate(string $contents): int
    {
        $offset = 0;
        while (($start = strpos($contents, '<', $offset)) !== false) {
            $tail = substr($contents, $start);
            $terminator = match (true) {
                str_starts_with($tail, '<!--') => '-->',
                str_starts_with($tail, '<?') => '?>',
                str_starts_with($tail, '<![CDATA[') => ']]>',
                default => null,
            };
            if ($terminator !== null) {
                $end = strpos($contents, $terminator, $start + strlen($terminator));
                if ($end === false) {
                    break;
                }
                $offset = $end + strlen($terminator);

                continue;
            }
            if (str_starts_with($tail, '<!')) {
                break;
            }
            if (preg_match('~\A<(?:[^<>\'\"]|\"[^\"]*\"|\'[^\']*\')*>~s', $tail, $match) !== 1) {
                break;
            }

            $tag = $match[0];
            $offset = $start + strlen($tag);
            if (preg_match('~^<ruleset(?:\s|>)~', $tag) === 1 && preg_match('~/\s*>$~', $tag) !== 1) {
                return $offset;
            }
        }

        throw new RuntimeException('could not recognize a non-self-closing ruleset opening element.');
    }
}
