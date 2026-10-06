import pandas as pd

from src.features.feature_pipeline import FEATURE_NAMES, extract_features
from src.features.text_features import extract_text_features
from src.features.url_features import extract_url_features


def test_feature_matrix_has_only_numeric_features_in_fixed_order():
    emails = pd.DataFrame(
        {
            "subject": ["URGENT", "hello"],
            "body": ["Visit https://a.example/x!", "No URL"],
            "label": [1, 0],
            "source": ["Nazario", "Enron"],
            "urls": [999, 999],
        }
    )
    before = emails.copy(deep=True)
    features = extract_features(emails)

    assert features.shape == (2, len(FEATURE_NAMES))
    assert tuple(features.columns) == FEATURE_NAMES
    assert all(pd.api.types.is_numeric_dtype(dtype) for dtype in features.dtypes)
    assert features["url_count"].tolist() == [1, 0]
    assert features["exclamation_count"].tolist() == [1, 0]
    assert "source" not in features and "label" not in features and "urls" not in features
    pd.testing.assert_frame_equal(emails, before)


def test_features_match_individual_extractors_using_the_same_combined_text():
    emails = pd.DataFrame({"subject": ["VERIFY"], "body": ["http://example.org!"]})
    expected = extract_text_features("VERIFY\n\nhttp://example.org!") | extract_url_features(
        "VERIFY\n\nhttp://example.org!"
    )
    assert extract_features(emails).iloc[0].to_dict() == expected


def test_batch_extraction_retains_input_order_and_matches_single_emails():
    emails = pd.DataFrame(
        {
            "subject": ["First", "Second", "Third"],
            "body": ["no link", "https://example.org", "urgent!"],
            "source": ["a", "b", "c"],
            "label": [0, 1, 0],
        },
        index=[17, 3, 99],
    )
    batch = extract_features(emails)
    singles = pd.concat(
        [extract_features(emails.iloc[[i]]) for i in range(len(emails))], ignore_index=True
    )
    pd.testing.assert_frame_equal(batch, singles)
    assert batch.index.tolist() == [0, 1, 2]


def test_empty_email_and_empty_table():
    features = extract_features(pd.DataFrame({"subject": [""], "body": [""]}))
    assert features.loc[0, "url_count"] == 0
    assert features.loc[0, "word_count"] == 0
    empty = extract_features(pd.DataFrame({"subject": [], "body": []}))
    assert empty.shape == (0, len(FEATURE_NAMES))
    assert all(pd.api.types.is_numeric_dtype(dtype) for dtype in empty.dtypes)
