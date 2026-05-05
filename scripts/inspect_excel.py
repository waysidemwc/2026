#!/usr/bin/env python3
"""Inspect the Excel file structure."""

import pandas as pd

excel_file = "export/Match schedule - Wayside Mini World Cup 2026.xlsx"
csv_file = "master_schedule_final.csv"

print("=" * 80)
print("EXCEL FILE")
print("=" * 80)
excel_df = pd.read_excel(excel_file)
print(f"\nShape: {excel_df.shape}")
print(f"\nColumns ({len(excel_df.columns)}):")
for i, col in enumerate(excel_df.columns, 1):
    print(f"  {i}. '{col}'")

print(f"\nFirst 5 rows:")
print(excel_df.head())

print("\n" + "=" * 80)
print("CSV FILE")
print("=" * 80)
csv_df = pd.read_csv(csv_file)
print(f"\nShape: {csv_df.shape}")
print(f"\nColumns ({len(csv_df.columns)}):")
for i, col in enumerate(csv_df.columns, 1):
    print(f"  {i}. '{col}'")

print(f"\nFirst 5 rows:")
print(csv_df.head())

print("\n" + "=" * 80)
print("COMPARISON")
print("=" * 80)
print("\nExtra columns in Excel:")
excel_cols = set(excel_df.columns)
csv_cols = set(csv_df.columns)
extra_in_excel = excel_cols - csv_cols
extra_in_csv = csv_cols - excel_cols

if extra_in_excel:
    for col in extra_in_excel:
        print(f"  - '{col}'")
        print(f"    Sample values: {excel_df[col].head().tolist()}")
else:
    print("  None")

if extra_in_csv:
    print("\nExtra columns in CSV:")
    for col in extra_in_csv:
        print(f"  - '{col}'")
else:
    print("\nNo extra columns in CSV")
