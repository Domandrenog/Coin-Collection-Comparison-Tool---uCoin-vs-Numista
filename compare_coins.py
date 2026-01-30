#!/usr/bin/env python3
"""
Script to compare coins and quantities between Excel files (ucoin.xlsx and numista.xlsx)
"""

import sys
from datetime import datetime

import pandas as pd


def load_excel(file):
    """Load Excel file and return a DataFrame"""
    try:
        if file.endswith(".xlsx"):
            df = pd.read_excel(file, engine="openpyxl")
        else:
            df = pd.read_excel(file)
        return df
    except Exception as e:
        print(f"Error loading {file}: {e}")
        sys.exit(1)


def normalize_for_comparison(s):
    """Normalize string for comparison (remove accents, convert to lowercase, etc)"""
    if pd.isna(s):
        return ""
    s = str(s).lower().strip()
    # Remove special characters
    s = s.replace("ã", "a").replace("á", "a").replace("à", "a")
    s = s.replace("é", "e").replace("ê", "e")
    s = s.replace("í", "i")
    s = s.replace("ó", "o").replace("õ", "o").replace("ô", "o")
    s = s.replace("ú", "u").replace("ü", "u")
    s = s.replace("ç", "c")

    # Normalize common country name variations
    if "united states" in s or s == "usa":
        return "usa"
    if "soviet union" in s or s == "ussr":
        return "ussr"

    return s


def normalize_reference(ref):
    """Normalize catalog reference for comparison"""
    if pd.isna(ref):
        return ""
    ref = str(ref).strip().upper()
    # Remove spaces and normalize separators
    ref = ref.replace(" ", "")
    # Remove variant letters that might appear (e.g., KM# A192 -> KM#192)
    # But keep letters at the end (e.g., KM# 164a)
    import re

    # Match pattern like KM# A123 and convert to KM#123
    ref = re.sub(r"(KM#|Y#)\s*A(\d+)", r"\1\2", ref)
    return ref


def extract_numbers(text):
    """Extract only numbers from text"""
    if pd.isna(text):
        return ""
    import re

    numbers = re.findall(r"\d+\.?\d*", str(text))
    return "".join(numbers)


def extract_diameter(diameter_str):
    """Extract numeric value from diameter"""
    if pd.isna(diameter_str):
        return None
    import re

    match = re.search(r"(\d+\.?\d*)", str(diameter_str))
    if match:
        try:
            return float(match.group(1))
        except:
            return None
    return None


def approximate_match(df1, df2):
    """
    Matching using mandatory criteria:
    1. Country/Issuer must match
    2. Year must match
    3. Diameter used as scoring factor
    4. Coin value compared by numbers only
    """
    matches = []
    matched_idx2 = set()

    for idx1, row1 in df1.iterrows():
        best_score = 0
        best_idx2 = None

        # Mandatory criteria from uCoin
        country1 = normalize_for_comparison(row1.get("country", ""))
        year1_raw = row1.get("year", "")

        # For Spanish coins, the real year may be in the var. column (year within the star)
        # The correct year is "19" + var. (e.g., var. = 77 → year = 1977)
        var1 = row1.get("var.", "")
        if (
            pd.notna(var1)
            and country1
            and ("spain" in country1 or "espanha" in country1)
        ):
            try:
                var_num = int(float(str(var1).strip()))
                year1 = 1900 + var_num
            except:
                # If var. is not valid, use normal year
                try:
                    year1 = (
                        int(float(str(year1_raw).strip()))
                        if pd.notna(year1_raw)
                        else None
                    )
                except:
                    year1 = None
        else:
            # For other coins, use normal year
            try:
                year1 = (
                    int(float(str(year1_raw).strip())) if pd.notna(year1_raw) else None
                )
            except:
                year1 = None

        diameter1 = extract_diameter(row1.get("diameter, mm", ""))
        value1_num = extract_numbers(row1.get("denomination", ""))

        # Skip if essential information is missing
        if not country1 or not year1:
            continue

        for idx2, row2 in df2.iterrows():
            if idx2 in matched_idx2:  # Avoid duplicates
                continue

            # Mandatory criteria from Numista
            issuer2 = normalize_for_comparison(row2.get("issuer", ""))
            country2 = normalize_for_comparison(row2.get("country", ""))

            # Try both years: "year" and "gregorian year"
            year_normal = row2.get("year", "")
            year_gregorian = row2.get("gregorian year", "")

            year2 = None
            year2_alt = None  # Alternative year for verification

            # Extract "ano"
            if (
                pd.notna(year_normal)
                and str(year_normal).strip()
                and str(year_normal).strip() != "nan"
            ):
                try:
                    year2 = int(float(str(year_normal).strip()))
                except:
                    pass

            # Extract "ano gregoriano"
            if (
                pd.notna(year_gregorian)
                and str(year_gregorian).strip()
                and str(year_gregorian).strip() != "nan"
            ):
                try:
                    year2_alt = int(float(str(year_gregorian).strip()))
                except:
                    pass

            # If we don't have year2, use the alternative
            if year2 is None:
                year2 = year2_alt
                year2_alt = None

            diameter2 = extract_diameter(row2.get("diameter", ""))
            value2_num = extract_numbers(row2.get("face value", ""))

            # Normalize values for comparison (convert decimals to integers if possible)
            # E.g., "0.05" -> "5" (5 cents), "0.5" -> "50" (50 cents), "1.0" -> "1"
            if value2_num:
                try:
                    val_float = float(value2_num)
                    if val_float < 1.0:
                        # It's cents - multiply by 100
                        value2_num = str(int(val_float * 100))
                    else:
                        # It's a whole unit
                        value2_num = str(int(val_float))
                except:
                    pass

            # MANDATORY CRITERIA

            # 1. Country must match (with flexibility for name variations)
            country_match = False
            if country1 and (issuer2 or country2):
                # Exact match
                if country1 == issuer2 or country1 == country2:
                    country_match = True
                # Match if one contains the other (any direction)
                elif issuer2 and (country1 in issuer2 or issuer2 in country1):
                    country_match = True
                elif country2 and (country1 in country2 or country2 in country1):
                    country_match = True

            if not country_match:
                continue  # MANDATORY

            # 2. Year must match (consider both "ano" and "ano gregoriano")
            year_match = False
            if year1 == year2:
                year_match = True
            elif year2_alt is not None and year1 == year2_alt:
                year_match = True

            if not year_match:
                continue  # MANDATORY

            # 3. Calculate diameter difference (if both available)
            diameter_diff = None
            if diameter1 is not None and diameter2 is not None:
                diameter_diff = abs(diameter1 - diameter2)

            # If we got here, mandatory criteria passed (country + year)
            score = 100  # Base score for mandatory criteria

            # Bonus/penalty for diameter
            if diameter_diff is not None:
                if diameter_diff <= 0.5:
                    score += 100  # Almost identical diameter - VERY HIGH WEIGHT
                elif diameter_diff <= 1.0:
                    score += 70  # Close diameter
                elif diameter_diff <= 2.0:
                    score += 40  # Acceptable diameter
                elif diameter_diff <= 3.5:
                    score += 10  # Reasonable diameter
                else:
                    # Very different diameter - big penalty
                    score -= 100  # Strong penalty

            # 4. Compare value (numbers only) - HIGH WEIGHT
            if value1_num and value2_num:
                if value1_num == value2_num:
                    score += 150  # Perfect value match
                elif value1_num in value2_num or value2_num in value1_num:
                    score += 50  # Partial match
            elif not value1_num and not value2_num:
                # Both without numeric value (rare but possible)
                score += 80

            # 5. Compare catalog reference (if available)
            ref1 = normalize_reference(row1.get("number", ""))
            ref2 = normalize_reference(row2.get("reference", ""))
            if ref1 and ref2:
                if ref1 == ref2:
                    score += 200  # Perfect reference match - VERY HIGH WEIGHT
                elif ref1 in ref2 or ref2 in ref1:
                    score += 80  # Partial reference match

            if score > best_score:
                best_score = score
                best_idx2 = idx2

        if best_idx2 is not None:
            matches.append(
                {"idx_ucoin": idx1, "idx_numista": best_idx2, "score": best_score}
            )
            matched_idx2.add(best_idx2)

    return matches


def group_duplicate_coins(df, type):
    """Group identical coins and sum quantities"""
    if type == "ucoin":
        # IMPORTANT: Adjust year based on var. column BEFORE grouping
        # For Spanish coins, var. represents the year within the star
        df = df.copy()
        if "var." in df.columns:
            for idx, row in df.iterrows():
                country = normalize_for_comparison(row.get("country", ""))
                var_val = row.get("var.", "")
                if (
                    pd.notna(var_val)
                    and country
                    and ("spain" in country or "espanha" in country)
                ):
                    try:
                        var_num = int(float(str(var_val).strip()))
                        # Real year is 1900 + var. (e.g., var. 77 → 1977)
                        df.at[idx, "year"] = 1900 + var_num
                    except:
                        pass

        # Identify key columns for grouping
        key_cols = ["country", "year", "denomination", "diameter, mm", "number"]
        key_cols = [c for c in key_cols if c in df.columns]

        # Group and sum quantities
        df_grouped = df.groupby(key_cols, dropna=False, as_index=False).agg(
            {"quantity": "sum"}
        )

        # Add other columns that may exist (take first value)
        for col in df.columns:
            if col not in key_cols and col != "quantity":
                df_temp = df.groupby(key_cols, dropna=False, as_index=False)[
                    col
                ].first()
                df_grouped = df_grouped.merge(df_temp, on=key_cols, how="left")

        return df_grouped
    else:  # numista
        # Identify key columns for grouping
        key_cols = [
            "issuer",
            "year",
            "gregorian year",
            "title",
            "diameter",
            "reference",
        ]
        key_cols = [c for c in key_cols if c in df.columns]

        # Group and sum quantities
        df_grouped = df.groupby(key_cols, dropna=False, as_index=False).agg(
            {"quantity": "sum"}
        )

        # Add other columns that may exist (take first value)
        for col in df.columns:
            if col not in key_cols and col != "quantity":
                df_temp = df.groupby(key_cols, dropna=False, as_index=False)[
                    col
                ].first()
                df_grouped = df_grouped.merge(df_temp, on=key_cols, how="left")

        return df_grouped


def compare_coins(df1, df2, name1, name2):
    """Compare two coin DataFrames"""
    print(f"\n{'='*80}")
    print(f"COMPARISON BETWEEN {name1.upper()} AND {name2.upper()}")
    print(f"{'='*80}\n")

    # Normalize column names
    df1.columns = df1.columns.str.strip().str.lower()
    df2.columns = df2.columns.str.strip().str.lower()

    # Show basic information BEFORE grouping
    print(f"📊 {name1} (original):")
    print(f"   - Total lines: {len(df1)}")
    total_qty_1_original = df1["quantity"].sum() if "quantity" in df1.columns else 0
    print(f"   - Total quantity: {int(total_qty_1_original)} coins\n")

    print(f"📊 {name2} (original):")
    print(f"   - Total lines: {len(df2)}")
    total_qty_2_original = df2["quantity"].sum() if "quantity" in df2.columns else 0
    print(f"   - Total quantity: {int(total_qty_2_original)} coins\n")

    # Group duplicate coins
    print("🔄 Grouping duplicate coins...")
    df1_original_len = len(df1)
    df2_original_len = len(df2)

    df1 = group_duplicate_coins(df1, "ucoin")
    df2 = group_duplicate_coins(df2, "numista")

    duplicates_1 = df1_original_len - len(df1)
    duplicates_2 = df2_original_len - len(df2)

    if duplicates_1 > 0:
        print(f"   ✓ {name1}: {duplicates_1} duplicate lines grouped")
    if duplicates_2 > 0:
        print(f"   ✓ {name2}: {duplicates_2} duplicate lines grouped")
    print()

    # Show basic information AFTER grouping
    print(f"📊 {name1} (grouped):")
    print(f"   - Total lines: {len(df1)}")
    print(
        f"   - Main columns: country, year, denomination, quantity, reference number\n"
    )

    print(f"📊 {name2}:")
    print(f"   - Total lines: {len(df2)}")
    print(f"   - Main columns: issuer, year, title, quantity, reference\n")

    # General statistics
    total_qty_1 = df1["quantity"].sum() if "quantity" in df1.columns else 0
    total_qty_2 = df2["quantity"].sum() if "quantity" in df2.columns else 0

    print(f"📈 Total quantities:")
    print(f"   - {name1}: {int(total_qty_1)} coins")
    print(f"   - {name2}: {int(total_qty_2)} coins")
    print(f"   - Difference: {int(total_qty_1 - total_qty_2)} coins\n")

    # Perform approximate matching
    print("🔄 Matching coins between files (this may take a while)...")
    matches = approximate_match(df1, df2)

    matched_idx1 = {m["idx_ucoin"] for m in matches}
    matched_idx2 = {m["idx_numista"] for m in matches}

    print(f"✅ Found {len(matches)} matches between files\n")

    # Unmatched coins
    unmatched_ucoin = df1[~df1.index.isin(matched_idx1)]
    unmatched_numista = df2[~df2.index.isin(matched_idx2)]

    print(f"\n{'='*80}")
    print("UNMATCHED COINS")
    print(f"{'='*80}\n")

    print(f"🔴 Only in {name1}: {len(unmatched_ucoin)} coins")
    print(f"🔴 Only in {name2}: {len(unmatched_numista)} coins\n")

    # Compare quantities of matched coins
    print(f"{'='*80}")
    print("QUANTITY COMPARISON (MATCHED COINS)")
    print(f"{'='*80}\n")

    differences = []
    equal_qty = 0

    for match in matches:
        idx1 = match["idx_ucoin"]
        idx2 = match["idx_numista"]

        row1 = df1.loc[idx1]
        row2 = df2.loc[idx2]

        qty1 = row1.get("quantity", 0)
        qty2 = row2.get("quantity", 0)

        if qty1 != qty2:
            differences.append(
                {
                    "country/issuer": row1.get("country", ""),
                    "year": row1.get("year", ""),
                    "denomination": row1.get("denomination", ""),
                    "ref_ucoin": row1.get("number", ""),
                    "ref_numista": row2.get("reference", ""),
                    "qty_ucoin": int(qty1) if pd.notna(qty1) else 0,
                    "qty_numista": int(qty2) if pd.notna(qty2) else 0,
                    "difference": (
                        int(qty1 - qty2) if pd.notna(qty1) and pd.notna(qty2) else 0
                    ),
                }
            )
        else:
            equal_qty += 1

    if differences:
        print(f"⚠️  Quantity differences: {len(differences)}")
        print(f"✅ Equal quantities: {equal_qty}\n")

        df_diff = pd.DataFrame(differences)
        print(df_diff.to_string(index=False))

        # Export to Excel
        filename = f"differences_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df_diff.to_excel(filename, index=False)
        print(f"\n💾 Differences saved to: {filename}")
    else:
        print(f"✅ All {len(matches)} matched coins have equal quantities!")

    # Analyze the difference
    print(f"\n{'='*80}")
    print("DETAILED DIFFERENCE ANALYSIS")
    print(f"{'='*80}\n")

    # Calculate contributions to total difference
    qty_unmatched_ucoin = (
        unmatched_ucoin["quantity"].sum() if len(unmatched_ucoin) > 0 else 0
    )
    qty_unmatched_numista = (
        unmatched_numista["quantity"].sum() if len(unmatched_numista) > 0 else 0
    )

    # Differences in matched coins
    positive_diffs = sum(d["difference"] for d in differences if d["difference"] > 0)
    negative_diffs = sum(d["difference"] for d in differences if d["difference"] < 0)

    print("📊 Contributions to total difference:\n")
    print(f"   Unmatched coins:")
    print(
        f"     • Only in uCoin: +{int(qty_unmatched_ucoin)} coins ({len(unmatched_ucoin)} types)"
    )
    print(
        f"     • Only in Numista: {int(qty_unmatched_numista)} coins ({len(unmatched_numista)} types)"
    )
    print(f"     • Sub-total: {int(qty_unmatched_ucoin - qty_unmatched_numista)}\n")

    print(f"   Matched coins with differences:")
    print(f"     • More in uCoin: +{int(positive_diffs)} coins")
    print(f"     • More in Numista: {int(negative_diffs)} coins")
    print(f"     • Sub-total: {int(positive_diffs + negative_diffs)}\n")

    final_total = int(
        qty_unmatched_ucoin - qty_unmatched_numista + positive_diffs + negative_diffs
    )
    print(f"   🎯 TOTAL: {final_total} more coins in uCoin\n")

    print(f"{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")

    # If the difference comes from matched coins
    if abs(positive_diffs + negative_diffs) <= 5:
        print("🔍 The difference comes from different quantities in matched coins:\n")
        relevant_coins = sorted(
            differences, key=lambda x: abs(x["difference"]), reverse=True
        )[:10]
        df_rel = pd.DataFrame(relevant_coins)
        print(
            df_rel[
                [
                    "country/issuer",
                    "year",
                    "denomination",
                    "ref_ucoin",
                    "qty_ucoin",
                    "qty_numista",
                    "difference",
                ]
            ].to_string(index=False)
        )

    # List all positive differences (coins missing in numista)
    coins_missing_numista = [d for d in differences if d["difference"] > 0]
    coins_extra_numista = [d for d in differences if d["difference"] < 0]

    print(f"\n\n📋 COMPLETE SUMMARY:\n")
    print(
        f"   • {len(coins_missing_numista)} coin types with more quantity in uCoin (+{int(positive_diffs)} units)"
    )
    print(
        f"   • {len(coins_extra_numista)} coin types with more quantity in Numista ({int(negative_diffs)} units)"
    )
    print(f"   • Net balance: {int(positive_diffs + negative_diffs)} coins")

    if coins_missing_numista:
        # Save only those missing
        filename_missing = (
            f"missing_in_numista_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        df_missing = pd.DataFrame(coins_missing_numista)
        df_missing.to_excel(filename_missing, index=False)
        print(f"\n💾 Coins with more quantity in uCoin: {filename_missing}")

    # Export unmatched coins
    if len(unmatched_ucoin) > 0 or len(unmatched_numista) > 0:
        filename2 = f"unmatched_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        with pd.ExcelWriter(filename2) as writer:
            if len(unmatched_ucoin) > 0:
                unmatched_ucoin[
                    ["country", "year", "denomination", "number", "quantity"]
                ].to_excel(writer, sheet_name="Only_uCoin", index=False)
            if len(unmatched_numista) > 0:
                unmatched_numista[
                    ["issuer", "year", "title", "reference", "quantity"]
                ].to_excel(writer, sheet_name="Only_Numista", index=False)
        print(f"💾 Unmatched coins saved to: {filename2}")


def main():
    file1 = "ucoin.xlsx"
    file2 = "numista.xlsx"

    print("🔄 Loading Excel files...")

    # Load files
    df_ucoin = load_excel(file1)
    df_numista = load_excel(file2)

    # Compare
    compare_coins(df_ucoin, df_numista, "ucoin", "numista")

    print("\n" + "=" * 80)
    print("✅ Comparison complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
