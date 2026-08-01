
# Data Cleaner

A command-line tool that cleans messy CSV/Excel files and generates a transparent report of every change made.

## Why this exists

"Clean my messy spreadsheet" is one of the most common freelance data requests. This tool automates the repetitive part while keeping a full audit trail — nothing is silently changed, every operation is logged.

## Features

- Standardizes inconsistent column names (`" Customer Name "` → `customer_name`)
- Strips leading/trailing whitespace from text fields
- Removes exact duplicate rows
- Handles missing values with multiple strategies: report-only, drop, mean, median
- Converts text-formatted numbers (`"$1,200.50"`) to proper numeric types
- Detects outliers using the IQR method (reports them, does not silently delete data)
- Generates a full text report of every transformation applied
- Supports both CSV and Excel (`.xlsx`) input/output

## Getting Started

### Requirements
```bash
pip install pandas openpyxl pytest
```

### Basic usage
```bash
python data_cleaner.py your_file.csv
```
This produces `your_file_cleaned.csv` in the same folder, and prints a report to the console.

### Full options
```bash
python data_cleaner.py input.csv \
  --output cleaned_output.csv \
  --missing mean \
  --report report.txt
```

| Flag | Description |
|---|---|
| `-o`, `--output` | Path for the cleaned file (default: `<input>_cleaned.csv`) |
| `--missing` | Strategy for missing values: `report`, `drop`, `mean`, `median` |
| `--report` | Save the text report to a file |

### Using it as a library
```python
from data_cleaner import DataCleaner

cleaner = DataCleaner.from_file("messy_data.csv")
cleaner.standardize_column_names().strip_whitespace().drop_duplicates()
cleaner.handle_missing(strategy="mean")
print(cleaner.summary_report())
cleaner.save("clean_data.csv")
```

### Run the tests
```bash
python -m pytest test_data_cleaner.py -v
```

## Example

Included: `sample_dirty_data.csv` — a realistic messy dataset (extra whitespace, inconsistent casing, currency-formatted numbers, duplicate rows, missing values).

```bash
python data_cleaner.py sample_dirty_data.csv --report cleaning_report.txt
```

## Project Structure
```
data-cleaner/
├── data_cleaner.py          # Core DataCleaner class + CLI
├── test_data_cleaner.py     # Unit tests (10 tests)
├── sample_dirty_data.csv    # Example messy dataset
└── README.md
```

## License
MIT

---
*Built as part of a Python/data-tools portfolio.*

# data-cleaner

