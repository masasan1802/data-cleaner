"""
Data Cleaner - A CLI tool for cleaning messy CSV/Excel datasets.

Handles common data quality problems:
- Missing values (multiple strategies)
- Duplicate rows
- Inconsistent column names
- Inconsistent text casing / whitespace
- Type coercion (numbers stored as text, etc.)
- Outlier detection (for reporting, not silent removal)

Author: [Your Name]
"""

import argparse
import sys
from pathlib import Path

import pandas as pd


class DataCleaner:
    """Cleans a dataframe and tracks every change made, for a transparent report."""

    def __init__(self, df: pd.DataFrame):
        self.original_df = df.copy()
        self.df = df.copy()
        self.log = []  # human-readable record of every operation

    # ---------- loading ----------
    @classmethod
    def from_file(cls, path: str, sheet_name=0):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
        elif path.suffix.lower() in (".xlsx", ".xls"):
            df = pd.read_excel(path, sheet_name=sheet_name)
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

        return cls(df)

    # ---------- cleaning steps ----------
    def standardize_column_names(self):
        before = list(self.df.columns)
        self.df.columns = (
            self.df.columns
            .str.strip()
            .str.lower()
            .str.replace(r"[^\w]+", "_", regex=True)
            .str.strip("_")
        )
        changed = sum(1 for a, b in zip(before, self.df.columns) if a != b)
        self.log.append(f"Standardized {changed} column name(s).")
        return self

    def strip_whitespace(self):
        text_cols = self.df.select_dtypes(include=["object", "string"]).columns
        for col in text_cols:
            self.df[col] = self.df[col].astype(str).str.strip()
        self.log.append(f"Stripped whitespace on {len(text_cols)} text column(s).")
        return self

    def drop_duplicates(self):
        before = len(self.df)
        self.df = self.df.drop_duplicates()
        removed = before - len(self.df)
        self.log.append(f"Removed {removed} duplicate row(s).")
        return self

    def handle_missing(self, strategy="report", columns=None, fill_value=None):
        """
        strategy:
          - 'report'  : do nothing, just count (default, safest)
          - 'drop'    : drop rows with any missing value in target columns
          - 'fill'    : fill missing values with fill_value
          - 'mean'    : fill numeric columns with column mean
          - 'median'  : fill numeric columns with column median
        """
        cols = columns or list(self.df.columns)
        missing_before = self.df[cols].isna().sum().sum()

        if strategy == "report":
            pass
        elif strategy == "drop":
            self.df = self.df.dropna(subset=cols)
        elif strategy == "fill":
            self.df[cols] = self.df[cols].fillna(fill_value)
        elif strategy in ("mean", "median"):
            for col in cols:
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    value = self.df[col].mean() if strategy == "mean" else self.df[col].median()
                    self.df[col] = self.df[col].fillna(value)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        missing_after = self.df[cols].isna().sum().sum() if strategy != "drop" else 0
        self.log.append(
            f"Missing values: {missing_before} found, strategy='{strategy}', "
            f"{missing_before - missing_after if strategy != 'drop' else missing_before} handled."
        )
        return self

    def coerce_numeric(self, columns):
        """Try to convert columns that look numeric but are stored as text."""
        converted = []
        for col in columns:
            if col not in self.df.columns:
                continue
            original = self.df[col]
            cleaned = pd.to_numeric(
                original.astype(str).str.replace(r"[,$%]", "", regex=True).str.strip(),
                errors="coerce",
            )
            success_rate = cleaned.notna().sum() / max(len(original), 1)
            if success_rate > 0.8:  # only apply if it mostly worked
                self.df[col] = cleaned
                converted.append(col)
        self.log.append(f"Converted {len(converted)} column(s) to numeric: {converted}")
        return self

    # ---------- reporting ----------
    def detect_outliers(self, column, method="iqr"):
        """Returns indices of likely outliers using the IQR method. Does not remove them."""
        if not pd.api.types.is_numeric_dtype(self.df[column]):
            return []
        q1, q3 = self.df[column].quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (self.df[column] < lower) | (self.df[column] > upper)
        return self.df.index[mask].tolist()

    def summary_report(self):
        report_lines = [
            "===== DATA CLEANING REPORT =====",
            f"Original rows: {len(self.original_df)}",
            f"Final rows: {len(self.df)}",
            f"Original columns: {len(self.original_df.columns)}",
            f"Final columns: {len(self.df.columns)}",
            "",
            "--- Operations performed ---",
        ]
        report_lines += [f"- {entry}" for entry in self.log]

        report_lines += ["", "--- Missing values by column (after cleaning) ---"]
        na_counts = self.df.isna().sum()
        for col, count in na_counts.items():
            if count > 0:
                report_lines.append(f"{col}: {count}")
        if na_counts.sum() == 0:
            report_lines.append("None")

        report_lines += ["", "--- Column data types ---"]
        for col, dtype in self.df.dtypes.items():
            report_lines.append(f"{col}: {dtype}")

        return "\n".join(report_lines)

    # ---------- output ----------
    def save(self, path):
        path = Path(path)
        if path.suffix.lower() == ".csv":
            self.df.to_csv(path, index=False)
        elif path.suffix.lower() in (".xlsx", ".xls"):
            self.df.to_excel(path, index=False)
        else:
            raise ValueError(f"Unsupported output type: {path.suffix}")


# ------------------- CLI layer -------------------

def build_arg_parser():
    parser = argparse.ArgumentParser(description="Clean a messy CSV/Excel file.")
    parser.add_argument("input", help="Path to input CSV or Excel file")
    parser.add_argument("-o", "--output", help="Path to save cleaned file", default=None)
    parser.add_argument(
        "--missing", choices=["report", "drop", "mean", "median"],
        default="report", help="Strategy for missing values (default: report only)"
    )
    parser.add_argument("--report", help="Path to save the text report", default=None)
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    try:
        cleaner = DataCleaner.from_file(args.input)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    (
        cleaner
        .standardize_column_names()
        .strip_whitespace()
        .drop_duplicates()
        .handle_missing(strategy=args.missing)
    )

    report = cleaner.summary_report()
    print(report)

    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
        print(f"\nReport saved to: {args.report}")

    output_path = args.output or (Path(args.input).stem + "_cleaned.csv")
    cleaner.save(output_path)
    print(f"Cleaned data saved to: {output_path}")


if __name__ == "__main__":
    main()
