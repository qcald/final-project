"""Checks that run on pasted text before any model sees it, and on model output after."""

import re

PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

# Phrases that try to give the model orders instead of describing a place.
INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above|earlier) (instructions|rules|prompts?)",
    r"disregard (the |your )?(instructions|rules|system prompt)",
    r"you are now",
    r"system prompt",
    r"new instructions?",
    r"always recommend",
    r"only recommend",
    r"do not (mention|list|recommend) (any )?other",
]
INJECTION = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)


def scrub_pii(text: str) -> tuple[str, int]:
    """Replace phone numbers and emails so friends' contact details never reach the model."""
    text, n_phone = PHONE.subn("[phone removed]", text)
    text, n_email = EMAIL.subn("[email removed]", text)
    return text, n_phone + n_email


def find_injection(text: str) -> list[str]:
    """Return the lines that look like prompt-injection attempts."""
    return [line.strip() for line in text.splitlines() if INJECTION.search(line)]


# Capitalized words that aren't place names, so they don't count as an unlisted mention
COMMON_CAPITALIZED = {
    "i", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july", "august", "september",
    "october", "november", "december", "portuguese", "mexican", "spanish", "italian", "french",
    "japanese", "american", "english", "start", "end", "day", "night", "morning", "afternoon", "evening",
}
_WORD = re.compile(r"[^\W\d_][\w'’-]*")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _words(text: str) -> set[str]:
    return {w.lower() for w in _WORD.findall(text)}


def strip_unlisted_mentions(text: str, allowed_text: str) -> tuple[str, list[str]]:
    """Remove sentences that name something capitalized (a likely place) that appears nowhere in
    `allowed_text` (the candidate places, cities, friends, their quotes, and the question).
    Returns the cleaned text and the removed sentences."""
    allowed = _words(allowed_text) | COMMON_CAPITALIZED
    kept, removed = [], []
    for sentence in _SENTENCE_END.split(text.strip()):
        words = _WORD.findall(sentence)
        # The first word is capitalized because it starts the sentence, so skip it
        # Plurals count too ("Sundays", "Tapas Bars"), so also try the word without a trailing s
        unknown = [w for w in words[1:] if w[0].isupper()
                   and w.lower() not in allowed and w.lower().removesuffix("s") not in allowed]
        (removed if unknown else kept).append(sentence)
    return " ".join(kept), removed
