"""Deterministic text cleaning for raw emails.

Everything here is a pure function of one string: it learns nothing from the
dataset, so running it before the train/val/test split cannot leak information.

What is deliberately KEPT: letter case, punctuation, URLs and paragraph breaks
(they carry phishing signal, e.g. SHOUTING, '!!!', link structure).
What is NOT done: quoted-printable decoding (its markers collide with ordinary
text such as '=====' lines and 'total = 5'), and U+FFFD removal (it cannot be
repaired and deleting it would glue words together).
"""

import html
import re

import pandas as pd

from src.data.loader import deduplicate_emails

# Only real HTML tag names are stripped. A generic "<anything>" pattern would
# also hit '<http://...>', '<user@host>' and '<what>' in ordinary email text.
_TAG_NAMES = (
    r"(?:html|head|body|title|meta|link|div|span|p|br|hr|a|b|i|u|em|strong|font"
    r"|center|table|thead|tbody|tr|td|th|ul|ol|li|img|h[1-6]|blockquote|pre"
    r"|form|input)"
)
# The name must be followed by whitespace, '/' or '>' so '<a@b.com>' is not a tag.
# {0,500} bounds the scan so a stray '<' cannot trigger runaway matching.
_TAG_RE = re.compile(rf"</?{_TAG_NAMES}(?=[\s/>])[^>]{{0,500}}>", re.IGNORECASE)
_ANCHOR_RE = re.compile(
    r"<a\s[^>]{0,500}?\bhref\s*=\s*[\"']?([^\"'\s>]+)[^>]{0,500}>", re.IGNORECASE
)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

# Only entities that end with ';' are decoded. html.unescape would also turn
# the '&copy' inside 'page?a=1&copy=2' into a copyright sign and corrupt URLs.
_ENTITY_RE = re.compile(r"&(?:#\d+|#x[0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]{1,31});")

# Mojibake = UTF-8 bytes wrongly decoded as cp1252. In that form a character is
# one 'lead' byte (0xC2-0xF4 -> 'Â'..'ô') followed by 1-3 'continuation' bytes
# (0x80-0xBF -> '€', '•', '£', '©', ...). Both sets are built from cp1252 itself.
_LEAD = "".join(bytes([b]).decode("cp1252") for b in range(0xC2, 0xF5))
_CONT = "".join(bytes([b]).decode("cp1252", errors="ignore") for b in range(0x80, 0xC0))
_MOJIBAKE_SEQ_RE = re.compile(f"[{_LEAD}][{_CONT}]{{1,3}}")
# Control chars (not \t \n \r) and zero-width characters.
_INVISIBLE_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200b\u200c\u200d\u2060\ufeff]")
_UNICODE_SPACE_RE = re.compile(r"[\xa0\u2000-\u200a\u202f\u205f\u3000]")
_INLINE_SPACE_RE = re.compile(r"[ \t]+")
_SPACE_AROUND_NEWLINE_RE = re.compile(r" ?\n ?")
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def _repair_sequence(match: re.Match) -> str:
    seq = match.group(0)
    # Try the longest candidate first, then shorter ones; leave it unchanged if
    # none is valid UTF-8. A wrong repair is therefore practically impossible.
    for end in range(len(seq), 1, -1):
        try:
            return seq[:end].encode("cp1252").decode("utf-8") + seq[end:]
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    return seq


def repair_mojibake(text: str) -> str:
    """Undo UTF-8 text that was wrongly decoded as cp1252 (e.g. 'â€¢' -> '•').

    Repairs each suspicious sequence on its own instead of the whole text, so
    genuine non-ASCII characters elsewhere in the email (e.g. a real '\\xa0' or
    'ü') do not block the repair, and a sequence that is not valid UTF-8 is
    left untouched.
    """
    return _MOJIBAKE_SEQ_RE.sub(_repair_sequence, text)


def strip_html(text: str) -> str:
    """Remove HTML comments and known tags, keeping the target of <a href=...>.

    Link targets are kept as visible text so URL features can still see them.
    """
    text = _COMMENT_RE.sub(" ", text)
    text = _ANCHOR_RE.sub(r" \1 ", text)
    return _TAG_RE.sub(" ", text)


def normalize_whitespace(text: str) -> str:
    """Normalize line endings and spacing; keep single and double newlines."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _INVISIBLE_RE.sub("", text)
    text = _UNICODE_SPACE_RE.sub(" ", text)
    text = _INLINE_SPACE_RE.sub(" ", text)
    text = _SPACE_AROUND_NEWLINE_RE.sub("\n", text)
    text = _BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()


def clean_text(text: str) -> str:
    """Clean one text field (typically an email body)."""
    # Invisible characters go first: one stray zero-width char next to garbled
    # text would make the strict mojibake round trip fail.
    text = _INVISIBLE_RE.sub("", text)
    text = repair_mojibake(text)
    text = strip_html(text)
    text = _ENTITY_RE.sub(lambda m: html.unescape(m.group(0)), text)
    return normalize_whitespace(text)


def clean_subject(text: str) -> str:
    """Clean a subject line: same as clean_text but forced onto a single line."""
    return " ".join(clean_text(text).split())


def clean_emails(emails: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with subject and body cleaned. Rows are not dropped."""
    cleaned = emails.copy()
    cleaned["subject"] = cleaned["subject"].map(clean_subject)
    cleaned["body"] = cleaned["body"].map(clean_text)
    return cleaned


def preprocess_emails(emails: pd.DataFrame) -> pd.DataFrame:
    """Clean every email, then drop exact duplicates of the cleaned text.

    Cleaning can make two different raw emails identical (e.g. they differed
    only in whitespace), so deduplication is repeated on the cleaned text. Both
    steps are deterministic and learn nothing from the data, so this is safe to
    run before the split.
    """
    return deduplicate_emails(clean_emails(emails))
