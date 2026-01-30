# Coin Collection Comparison Tool

A Python script to compare two coin collections from Excel files (uCoin and Numista) and identify differences in coins and quantities.

**Supports Excel files in both English and Portuguese (PT-PT)** - column names are automatically detected regardless of language.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Exporting Your Collections](#exporting-your-collections)
  - [Exporting from uCoin](#exporting-from-ucoin)
  - [Exporting from Numista](#exporting-from-numista)
- [Usage](#usage)
- [Expected Excel File Structure](#expected-excel-file-structure)
- [Matching Algorithm](#matching-algorithm)
- [Special Features](#special-features)
  - [Country Name Normalization](#country-name-normalization)
  - [Catalog Reference Normalization](#catalog-reference-normalization)
  - [Spanish Coins with "Var." Field](#spanish-coins-with-var-field)
  - [Duplicate Grouping](#duplicate-grouping)
- [Output Reports](#output-reports)
- [Console Output](#console-output)
- [Example Output](#example-output)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Contributing](#contributing)

## Features

- **Intelligent Matching Algorithm**: Matches coins based on mandatory criteria (country, year, diameter) with a sophisticated scoring system
- **Duplicate Grouping**: Automatically groups duplicate entries and sums their quantities
- **Spanish Coin Variant Handling**: Special logic for Spanish coins with "var." field (year within the star)
- **Flexible Country Matching**: Handles country name variations (e.g., "United States" vs "United States of America")
- **Dual Year Support**: Checks both "year" and "gregorian year" fields from Numista
- **Value Normalization**: Converts decimal values to integers for proper comparison (0.05 → 5 cents)
- **Diameter Tolerance**: Uses diameter as a scoring factor rather than strict requirement
- **Detailed Reports**: Generates Excel files with differences, unmatched coins, and analysis

## Requirements

- Python 3.8 or higher
- pandas
- openpyxl
- xlrd

## Installation

1. Clone or download this repository
2. Create a virtual environment (recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Linux/Mac
   # or
   .venv\Scripts\activate  # On Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Exporting Your Collections

Before using the comparison tool, you need to export your collections from both websites.

### Exporting from uCoin

1. **Select Language**: Scroll to the bottom of the uCoin page and choose your preferred language (English or Portuguese)
2. **Go to My Collection**: Click on "My collection" in the top navigation menu
3. **Export Tab**: Click on the "Export" tab
4. **Download**: Click on "Microsoft Excel (XLS)" button
5. **Save**: Save the file as `ucoin.xlsx` in the same directory as the script

### Exporting from Numista

1. **Go to My Collection**: Navigate to your collection page ("My collection" / "Minha coleção")
2. **Scroll Down**: Scroll to the bottom of the page
3. **Export Button**: Click on "Export my collection" / "Exportar minha coleção"
4. **Select Options**:
   - **Type** (Tipo): Select "Coins" / "Moedas"
   - **Columns** (Colunas): Select the following columns:
     - País / Country
     - Emissor / Issuer
     - Ano / Year
     - Ano Gregoriano / Gregorian Year
     - Título / Title
     - Valor de face / Face Value
     - Diâmetro / Diameter
     - Referência / Reference
     - Quantidade / Quantity
   - **Language**: Choose Portuguese or English
   - **Format**: Select "XLSX"
5. **Download**: Click export and save the file as `numista.xlsx` in the same directory as the script

**Important**: Both files MUST use the same language - either both in English or both in Portuguese. The script cannot handle mixed languages (one file in English and another in Portuguese).

## Usage

1. Place your exported Excel files in the same directory as the script:
   - `ucoin.xlsx` - Your uCoin collection export
   - `numista.xlsx` - Your Numista collection export

2. Run the script:
   ```bash
   # Portuguese version
   python comparar_moedas.py
   
   # English version
   python compare_coins.py
   ```
   
   **Note**: Both scripts are functionally identical. Choose based on your preference:
   - `comparar_moedas.py` - Portuguese code and output messages
   - `compare_coins.py` - English code and output messages

3. The script will generate output files with timestamps:
   
   **Portuguese version output:**
   - `diferencas_YYYYMMDD_HHMMSS.xlsx` - Coins with quantity differences
   - `faltam_em_numista_YYYYMMDD_HHMMSS.xlsx` - Coins with more quantity in uCoin
   - `nao_correspondidas_YYYYMMDD_HHMMSS.xlsx` - Unmatched coins (two sheets)
   
   **English version output:**
   - `differences_YYYYMMDD_HHMMSS.xlsx` - Coins with quantity differences
   - `missing_in_numista_YYYYMMDD_HHMMSS.xlsx` - Coins with more quantity in uCoin
   - `unmatched_YYYYMMDD_HHMMSS.xlsx` - Unmatched coins (two sheets)

## Expected Excel File Structure

**The script automatically detects column names in both English and Portuguese (PT-PT).**

### uCoin file (ucoin.xlsx)
Required columns (English / Portuguese):
- `Country` / `País` - Country name
- `Year` / `Ano` - Year
- `Var.` - Variant (for Spanish coins with year in star)
- `Denomination` / `Denominação` - Coin denomination/value
- `Diameter, mm` / `Diâmetro, mm` - Diameter in mm
- `Number` / `Número` - Catalog reference (e.g., KM# 123)
- `Quantity` / `Quantidade` - Quantity

### Numista file (numista.xlsx)
Required columns (English / Portuguese):
- `Issuer` / `Emissor` or `Country` / `País` - Issuer/Country name
- `Year` / `Ano` - Year
- `Gregorian Year` / `Ano Gregoriano` - Gregorian year (used when "Year"/"Ano" differs)
- `Title` / `Título` or `Face Value` / `Valor de face` - Title or face value
- `Diameter` / `Diâmetro` - Diameter in mm
- `Reference` / `Referência` - Catalog reference
- `Quantity` / `Quantidade` - Quantity

**Note**: The script normalizes column names during processing, so minor variations in spacing or capitalization are handled automatically.

## Matching Algorithm

The script uses a sophisticated scoring system with the following criteria:

### Mandatory Criteria (must match):
1. **Country**: Country/Issuer name with intelligent normalization:
   - Handles variations: "USA" ↔ "United States"
   - Handles variations: "USSR" ↔ "Soviet Union"
   - Flexible substring matching for other countries
2. **Year**: Must match exactly (checks both "year" and "gregorian year" columns)

### Scoring Factors:
1. **Catalog Reference** (NEW - highest weight):
   - Perfect match: +200 points
   - Partial match: +80 points
   - Normalizes references: "KM# A192" ↔ "KM# 192"

2. **Diameter similarity**:
   - ≤ 0.5mm difference: +100 points
   - ≤ 1.0mm difference: +70 points
   - ≤ 2.0mm difference: +40 points
   - ≤ 3.5mm difference: +10 points
   - > 3.5mm difference: -100 points (penalty)

3. **Value match**:
   - Perfect match: +150 points
   - Partial match: +50 points
   - No value in both: +80 points

The coin pair with the highest score above the threshold is selected as a match.

## Special Features

### Country Name Normalization
The script automatically normalizes common country name variations:
- **USA**: Matches "USA", "United States", "United States of America"
- **USSR**: Matches "USSR", "URSS", "Soviet Union", "União Soviética"
- Other countries use flexible substring matching

### Catalog Reference Normalization
Catalog references are intelligently normalized:
- Removes variant prefixes: "KM# A192" matches "KM# 192"
- Preserves suffix letters: "KM# 164a" remains distinct from "KM# 164"
- Normalizes spacing and capitalization
- Reference matching has the highest weight in the scoring system

### Spanish Coins with "Var." Field
Spanish coins often have a "var." field indicating the year within the star on the coin. The script automatically:
- Detects Spanish coins with "var." value
- Calculates the real year as 1900 + var (e.g., var=77 → year 1977)
- Uses this calculated year for matching

### Duplicate Grouping
Before matching, the script groups duplicate entries based on:
- Country
- Year (after applying var. conversion for Spanish coins)
- Denomination
- Diameter
- Catalog reference

Quantities are automatically summed for identical coins.

## Output Reports

### 1. Differences Report (differences_*.xlsx / diferencas_*.xlsx)
Lists coins that exist in both collections but have different quantities:
- Country/Issuer
- Year
- Denomination
- Catalog references from both sources
- Quantities from both sources
- Difference (positive = more in uCoin, negative = more in Numista)

### 2. Missing in Numista Report (missing_in_numista_*.xlsx / faltam_em_numista_*.xlsx)
Lists coins with higher quantity in uCoin than Numista.

### 3. Unmatched Coins Report (unmatched_*.xlsx / nao_correspondidas_*.xlsx)
Two sheets:
- **Only_uCoin** / **Apenas_uCoin**: Coins only found in uCoin collection
- **Only_Numista** / **Apenas_Numista**: Coins only found in Numista collection

## Console Output

The script provides detailed console output including:
- Original and grouped file statistics
- Number of duplicate lines grouped
- Total quantities comparison
- Number of matches found
- Unmatched coins count
- Detailed breakdown of quantity differences
- Analysis of the net difference

## Example Output

```
================================================================================
COMPARISON BETWEEN UCOIN AND NUMISTA
================================================================================

📊 ucoin (original):
   - Total lines: 870
   - Total quantity: 1173 coins

📊 numista (original):
   - Total lines: 866
   - Total quantity: 1172 coins

🔄 Grouping duplicate coins...
   ✓ ucoin: 11 duplicate lines grouped
   ✓ numista: 10 duplicate lines grouped

📊 ucoin (grouped):
   - Total lines: 859

🔄 Matching coins between files (this may take a while)...
✅ Found 856 matches between files

🔴 Only in ucoin: 3 coins
🔴 Only in numista: 3 coins

⚠️  Quantity differences: 2
✅ Equal quantities: 851

🎯 TOTAL: 1 more coins in uCoin
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Make sure you installed all dependencies with `pip install -r requirements.txt`

2. **File not found**: Ensure `ucoin.xlsx` and `numista.xlsx` are in the same directory as the script

3. **Column name errors**: Check that your Excel files have the expected column names (case-insensitive, but spelling must match)

4. **Many unmatched coins**: This could be due to:
   - Different years in the two collections
   - Different country name formats
   - Very different diameter values
   - Missing data in key columns

## License

This project is provided as-is for personal use.

## Contributing

Feel free to submit issues or pull requests if you find bugs or have suggestions for improvements.
