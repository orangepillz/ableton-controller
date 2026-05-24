"""Small text matching helpers for personalized copilot planning."""

from __future__ import annotations

import re


STOPWORDS = {"a", "an", "and", "for", "into", "of", "on", "the", "to", "with"}


def matched_terms(query: str, terms: list[str], *, allow_keyword_overlap: bool = False) -> list[str]:
    normalized_query, query_tokens, compact_query = query_forms(query)
    return sorted(
        {
            term
            for term in terms
            if term_matches(term, normalized_query, query_tokens, compact_query, allow_keyword_overlap=allow_keyword_overlap)
        }
    )


def term_matches(
    term: str,
    normalized_query: str,
    query_tokens: set[str],
    compact_query: str,
    *,
    allow_keyword_overlap: bool = False,
) -> bool:
    normalized_term = normalize(term)
    if not normalized_term:
        return False
    term_tokens = keyword_tokens(normalized_term.split())
    compact_term = normalized_term.replace(" ", "")
    compact_term_key = compact_key(term_tokens)
    compact_query_key = compact_key(normalized_query.split())
    if len(compact_term) <= 2:
        return compact_term in query_tokens
    if " " in normalized_term and f" {normalized_term} " in normalized_query:
        return True
    if allow_keyword_overlap and len(term_tokens) >= 3 and len(set(term_tokens).intersection(query_tokens)) >= 2:
        return True
    if compact_term in compact_query or compact_term_key in compact_query_key:
        return True
    return any(token == compact_term or token.rstrip("s") == compact_term for token in query_tokens)


def query_forms(query: str) -> tuple[str, set[str], str]:
    normalized = f" {normalize(query)} "
    ordered_tokens = normalized.split()
    return normalized, set(ordered_tokens), "".join(ordered_tokens)


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def compact_key(tokens: list[str]) -> str:
    return "".join(keyword_tokens(tokens))


def keyword_tokens(tokens: list[str]) -> list[str]:
    return [token for token in tokens if token and token not in STOPWORDS]
