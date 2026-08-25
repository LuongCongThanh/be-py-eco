"""Match a browser's `Accept-Language` header against the locales a
Supported Country allows.

Promoted out of `suggest_locale` and into its own module because it had
been copied, twice and slightly wrong, into `catalog` and `search`'s
Storefront views: both hardcoded `("vi", "en")` instead of reading the
Supported Country, so adding a locale meant editing three places and
getting two of them wrong was silent. This is now the only implementation
in the repository.

Takes the raw header string rather than a request: the matching has
nothing to do with HTTP plumbing, and a plain string is far easier to
table-test.
"""

from __future__ import annotations


def best_locale_match(accept_language: str, allowed_locales: list[str]) -> str | None:
    """First allowed locale named in `accept_language`, or None.

    Quality values are parsed off but not ordered by — header order wins,
    which is what browsers send in preference order anyway.
    """
    for part in accept_language.split(","):
        lang = part.split(";")[0].strip().split("-")[0].lower()
        if lang in allowed_locales:
            return lang
    return None
