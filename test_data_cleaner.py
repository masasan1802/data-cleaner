"""Unit tests for DataCleaner. Run with: python -m pytest test_data_cleaner.py -v"""

import pandas as pd
import pytest
from data_cleaner import DataCleaner


@pytest.fixture
def messy_df():
    return pd.DataFrame({
        " Name ": ["Alice", "bob", "Alice", "Carol"],
        "Amount ($)": ["$1,200.50", "850.00", "$1,200.50", None],
        "Age": [30, None, 30, 45],
    })


def test_standardize_column_names(messy_df):
    cleaner = DataCleaner(messy_df)
    cleaner.standardize_column_names()
    assert list(cleaner.df.columns) == ["name", "amount", "age"]


def test_strip_whitespace():
    df = pd.DataFrame({"name": ["  Alice  ", "Bob "]})
    cleaner = DataCleaner(df)
    cleaner.strip_whitespace()
    assert cleaner.df["name"].tolist() == ["Alice", "Bob"]


def test_drop_duplicates(messy_df):
    cleaner = DataCleaner(messy_df)
    cleaner.drop_duplicates()
    assert len(cleaner.df) == 3  # one exact duplicate row removed


def test_handle_missing_report_does_not_change_data(messy_df):
    cleaner = DataCleaner(messy_df)
    cleaner.handle_missing(strategy="report")
    assert len(cleaner.df) == len(messy_df)  # untouched
    assert cleaner.df.isna().sum().sum() > 0  # still has missing values


def test_handle_missing_drop():
    df = pd.DataFrame({"a": [1, None, 3]})
    cleaner = DataCleaner(df)
    cleaner.handle_missing(strategy="drop")
    assert len(cleaner.df) == 2


def test_handle_missing_mean():
    df = pd.DataFrame({"a": [10.0, None, 30.0]})
    cleaner = DataCleaner(df)
    cleaner.handle_missing(strategy="mean")
    assert cleaner.df["a"].isna().sum() == 0
    assert cleaner.df["a"].iloc[1] == 20.0  # mean of 10 and 30


def test_coerce_numeric():
    df = pd.DataFrame({"price": ["$1,200.50", "$850.00", "$2,300.00"]})
    cleaner = DataCleaner(df)
    cleaner.coerce_numeric(["price"])
    assert pd.api.types.is_numeric_dtype(cleaner.df["price"])
    assert cleaner.df["price"].iloc[0] == 1200.50


def test_detect_outliers():
    df = pd.DataFrame({"value": [10, 12, 11, 13, 12, 1000]})
    cleaner = DataCleaner(df)
    outliers = cleaner.detect_outliers("value")
    assert 5 in outliers  # the 1000 row


def test_summary_report_contains_key_sections(messy_df):
    cleaner = DataCleaner(messy_df)
    cleaner.standardize_column_names().drop_duplicates()
    report = cleaner.summary_report()
    assert "DATA CLEANING REPORT" in report
    assert "Operations performed" in report


def test_full_pipeline_from_csv(tmp_path):
    csv_content = "Name,Age\nAlice,30\nAlice,30\nBob,\n"
    csv_path = tmp_path / "test.csv"
    csv_path.write_text(csv_content)

    cleaner = DataCleaner.from_file(str(csv_path))
    cleaner.standardize_column_names().drop_duplicates().handle_missing(strategy="report")

    assert len(cleaner.df) == 2  # duplicate removed
    assert "name" in cleaner.df.columns
