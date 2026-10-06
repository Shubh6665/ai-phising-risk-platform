import pandas as pd

from src.data.preprocessor import (
    clean_emails,
    clean_subject,
    clean_text,
    normalize_whitespace,
    preprocess_emails,
    repair_mojibake,
    strip_html,
)


def test_clean_text_keeps_case_punctuation_and_url():
    raw = "URGENT!!! Verify at http://Example.com/Login?a=1 NOW"
    assert clean_text(raw) == raw


def test_strip_html_removes_known_tags_and_comments():
    raw = "<html><body><p>Hello <b>user</b></p><!-- hidden --></body></html>"
    assert " ".join(strip_html(raw).split()) == "Hello user"


def test_strip_html_keeps_href_target():
    raw = '<a href="http://evil.example/x" class="btn">Click here</a>'
    out = " ".join(strip_html(raw).split())
    assert out == "http://evil.example/x Click here"


def test_strip_html_leaves_non_html_angle_brackets():
    raw = "From: <john@example.com> see <http://example.com/a> and <what> <a@b.com>"
    assert strip_html(raw) == raw


def test_strip_html_is_case_insensitive():
    assert " ".join(strip_html("<DIV>Hi</DIV>").split()) == "Hi"


def test_entities_with_semicolon_are_decoded():
    assert clean_text("Tom &amp; Jerry&nbsp;&#169; &lt;3") == "Tom & Jerry © <3"


def test_entity_without_semicolon_in_url_is_not_corrupted():
    url = "http://example.com/page?a=1&copy=2&reg=3"
    assert clean_text(url) == url


def test_repair_mojibake_fixes_clean_case():
    assert repair_mojibake("ZÃ¼rich") == "Zürich"
    assert repair_mojibake("â€¢ item") == "• item"


def test_repair_mojibake_leaves_unrepairable_and_normal_text_untouched():
    assert repair_mojibake("plain ascii") == "plain ascii"
    assert repair_mojibake("Café already fine") == "Café already fine"
    # Per-sequence repair: a genuine 'ü' elsewhere must not block the repair.
    assert repair_mojibake("Zürich and ZÃ¼rich") == "Zürich and Zürich"
    # An incomplete sequence ('â€' needs a third byte) and a lone lead char stay as is.
    assert repair_mojibake("â€ x") == "â€ x"
    assert repair_mojibake("Â alone") == "Â alone"


def test_normalize_whitespace_line_endings_and_runs():
    raw = "a\r\nb\rc   d\t\te  \n\n\n\n\nf"
    assert normalize_whitespace(raw) == "a\nb\nc d e\n\nf"


def test_invisible_and_unicode_spaces_removed():
    raw = "pass\u200bword\x00 reset\xa0now\ufeff"
    assert normalize_whitespace(raw) == "password reset now"


def test_replacement_character_is_kept():
    assert "\ufffd" in clean_text("caf\ufffd")


def test_quoted_printable_like_text_is_not_decoded():
    raw = "total supply = 5\n=========\ncharset=3D\"utf-8\""
    assert clean_text(raw) == raw


def test_mojibake_is_repaired_even_with_adjacent_invisible_char():
    # Regression: found on real data (Nazario / Nigerian_Fraud). A zero-width
    # char made the first pass skip the repair, so cleaning was not idempotent.
    raw = "Sum of Â£26.5 million\u200b"
    assert clean_text(raw) == "Sum of £26.5 million"
    assert clean_text(clean_text(raw)) == clean_text(raw)


def test_double_escaped_entity_is_decoded_exactly_once():
    # Found in a Nazario email: pdf&amp;amp;jpeg. Never recursively decode:
    # doing so could reveal encoded markup or alter URL query strings.
    raw = "IMG-Invoice.pdf&amp;amp;jpeg"
    once = clean_text(raw)
    assert once == "IMG-Invoice.pdf&amp;jpeg"
    assert clean_text(once) == "IMG-Invoice.pdf&jpeg"  # known non-idempotent case
    assert clean_text("&amp;lt;script&amp;gt;") == "&lt;script&gt;"


def test_malformed_entity_is_left_alone():
    assert clean_text("a&nbs;b &quo;") == "a&nbs;b &quo;"


def test_mojibake_repaired_next_to_genuine_nbsp():
    # Regression: real emails mix a genuine NBSP with mojibake; the NBSP then
    # becomes a normal space and the mojibake is repaired in the same pass.
    raw = "Attention!\xa0 Sum of Â£26.5 million Â© 2019"
    assert clean_text(raw) == "Attention! Sum of £26.5 million © 2019"
    assert clean_text(clean_text(raw)) == clean_text(raw)


def test_clean_subject_is_single_line():
    assert clean_subject("Re:\r\n  your   account\n") == "Re: your account"


def test_clean_text_is_idempotent():
    raw = '<p>Hi&nbsp;there</p>\r\n\r\n\r\n<a href="http://x.example">link</a>  '
    once = clean_text(raw)
    assert clean_text(once) == once


def test_clean_emails_does_not_mutate_or_drop_rows():
    emails = pd.DataFrame(
        {
            "subject": ["Hi \n there"],
            "body": ["<b>Body</b>"],
            "label": [1],
            "source": ["Enron"],
        }
    )
    before = emails.copy()
    cleaned = clean_emails(emails)

    pd.testing.assert_frame_equal(emails, before)
    assert len(cleaned) == 1
    assert cleaned.loc[0, "subject"] == "Hi there"
    assert cleaned.loc[0, "body"] == "Body"
    assert list(cleaned.columns) == list(emails.columns)


def test_preprocess_dedups_rows_that_only_differ_in_noise():
    emails = pd.DataFrame(
        {
            "subject": ["Hello", "Hello"],
            "body": ["Same  text\r\n", "Same text"],
            "label": [1, 1],
            "source": ["Enron", "Ling"],
        }
    )
    result = preprocess_emails(emails)

    assert len(result) == 1
    assert result.loc[0, "source"] == "Enron"
