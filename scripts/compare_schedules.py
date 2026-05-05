#!/usr/bin/env python3
"""Compare master_schedule_final.csv with the exported Excel file."""

import pandas as pd
import sys

# Read the CSV file
csv_file = "master_schedule_final.csv"
excel_file = "export/Match schedule - Wayside Mini World Cup 2026.xlsx"

print(f"Reading CSV file: {csv_file}")
csv_df = pd.read_csv(csv_file)

print(f"Reading Excel file: {excel_file}")
excel_df = pd.read_excel(excel_file)

print(f"\nCSV shape: {csv_df.shape}")
print(f"Excel shape: {excel_df.shape}")

# Check if shapes match
if csv_df.shape != excel_df.shape:
    print(f"\n❌ ERROR: Different number of rows or columns!")
    print(f"   CSV: {csv_df.shape[0]} rows, {csv_df.shape[1]} columns")
    print(f"   Excel: {excel_df.shape[0]} rows, {excel_df.shape[1]} columns")
    sys.exit(1)

print(f"\n✓ Both files have {csv_df.shape[0]} rows and {csv_df.shape[1]} columns")

# Check column names
print("\nColumn names:")
print(f"CSV columns: {list(csv_df.columns)}")
print(f"Excel columns: {list(excel_df.columns)}")

if list(csv_df.columns) != list(excel_df.columns):
    print("\n❌ ERROR: Column names don't match!")
    sys.exit(1)

print("✓ Column names match")

# Compare data row by row
mismatches = []
for idx in range(len(csv_df)):
    for col in csv_df.columns:
        csv_val = str(csv_df.iloc[idx][col]).strip()
        excel_val = str(excel_df.iloc[idx][col]).strip()

        if csv_val != excel_val:
            mismatches.append({
                'row': idx + 2,  # +2 because row 1 is header, and we're 0-indexed
                'column': col,
                'csv_value': csv_val,
                'excel_value': excel_val
            })

if mismatches:
    print(f"\n❌ Found {len(mismatches)} mismatches:")
    for m in mismatches[:20]:  # Show first 20 mismatches
        print(f"\n  Row {m['row']}, Column '{m['column']}':")
        print(f"    CSV:   '{m['csv_value']}'")
        print(f"    Excel: '{m['excel_value']}'")

    if len(mismatches) > 20:
        print(f"\n  ... and {len(mismatches) - 20} more mismatches")
    sys.exit(1)
else:
    print("\n✅ SUCCESS: All entries match perfectly!")
    print(f"   Verified {csv_df.shape[0]} rows × {csv_df.shape[1]} columns")

# Show a sample of the data
print("\nSample data (first 5 rows):")
print(csv_df.head())
