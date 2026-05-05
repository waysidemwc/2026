#!/usr/bin/env python3
"""Verify that the Excel export matches the CSV master schedule."""

import pandas as pd
import sys
from datetime import datetime

excel_file = "export/Match schedule - Wayside Mini World Cup 2026.xlsx"
csv_file = "master_schedule_final.csv"

print("=" * 80)
print("VERIFYING EXPORT")
print("=" * 80)

# Read both files
csv_df = pd.read_csv(csv_file)
excel_df = pd.read_excel(excel_file)

print(f"\nCSV rows: {len(csv_df)}")
print(f"Excel rows: {len(excel_df)}")

if len(csv_df) != len(excel_df):
    print(f"\n❌ ERROR: Different number of rows!")
    sys.exit(1)

print("✓ Same number of rows")

# Map the time labels to actual dates
# "Tue 6:30-6:45" should map to Tuesday, June 16, 2026 at 18:30
# "Thu 6:30-6:45" should map to Thursday, June 18, 2026 at 18:30

def parse_time_label(time_label):
    """Parse time label like 'Tue 6:30-6:45' into day and start/end times."""
    parts = time_label.split()
    day = parts[0]  # 'Tue' or 'Thu'
    times = parts[1].split('-')
    start_time = times[0]  # '6:30'
    end_time = times[1] if len(times) > 1 else None  # '6:45'

    # Convert to 24-hour format (assuming PM)
    hour, minute = map(int, start_time.split(':'))
    if hour < 12:
        hour += 12
    start_24 = f"{hour:02d}:{minute:02d}"

    if end_time:
        hour, minute = map(int, end_time.split(':'))
        if hour < 12:
            hour += 12
        end_24 = f"{hour:02d}:{minute:02d}"
    else:
        end_24 = None

    # Map day to date
    day_to_date = {
        'Tue': '06-16-2026',
        'Thu': '06-18-2026'
    }

    return day_to_date.get(day), start_24, end_24

# Verify each row
errors = []
for idx in range(len(csv_df)):
    csv_row = csv_df.iloc[idx]
    excel_row = excel_df.iloc[idx]

    # Parse CSV time label
    expected_date, expected_start, expected_end = parse_time_label(csv_row['time_label'])

    # Check Division (age_group)
    if str(excel_row['Division']) != str(csv_row['age_group']):
        errors.append({
            'row': idx + 2,
            'field': 'Division/age_group',
            'csv': csv_row['age_group'],
            'excel': excel_row['Division']
        })

    # Check Day
    if str(excel_row['Day']) != expected_date:
        errors.append({
            'row': idx + 2,
            'field': 'Day',
            'csv': expected_date,
            'excel': excel_row['Day']
        })

    # Check Starting time
    if str(excel_row['Starting time']) != expected_start:
        errors.append({
            'row': idx + 2,
            'field': 'Starting time',
            'csv': expected_start,
            'excel': excel_row['Starting time']
        })

    # Check Playing field (zone + pitch_name)
    expected_field = f"{csv_row['zone']} {csv_row['pitch_name']}"
    if str(excel_row['Playing field']).strip() != expected_field.strip():
        errors.append({
            'row': idx + 2,
            'field': 'Playing field',
            'csv': expected_field,
            'excel': excel_row['Playing field']
        })

    # Check Team 1
    if str(excel_row['Team 1']).strip() != str(csv_row['team1']).strip():
        errors.append({
            'row': idx + 2,
            'field': 'Team 1',
            'csv': csv_row['team1'],
            'excel': excel_row['Team 1']
        })

    # Check Team 2
    if str(excel_row['Team 2']).strip() != str(csv_row['team2']).strip():
        errors.append({
            'row': idx + 2,
            'field': 'Team 2',
            'csv': csv_row['team2'],
            'excel': excel_row['Team 2']
        })

# Report results
print(f"\n{'=' * 80}")
print("VERIFICATION RESULTS")
print("=" * 80)

if errors:
    print(f"\n❌ Found {len(errors)} mismatches:")
    for i, err in enumerate(errors[:20], 1):
        print(f"\n{i}. Row {err['row']}, Field: {err['field']}")
        print(f"   CSV expects:  '{err['csv']}'")
        print(f"   Excel has:    '{err['excel']}'")

    if len(errors) > 20:
        print(f"\n... and {len(errors) - 20} more errors")

    sys.exit(1)
else:
    print("\n✅ SUCCESS: All entries match!")
    print(f"\n   Verified {len(csv_df)} matches across:")
    print(f"   - Division (age group)")
    print(f"   - Day and starting time")
    print(f"   - Playing field")
    print(f"   - Team 1 and Team 2")

    # Show summary stats
    print(f"\n   Age groups: {csv_df['age_group'].nunique()}")
    print(f"   Unique teams: {len(set(csv_df['team1'].tolist() + csv_df['team2'].tolist()))}")
    print(f"   Time slots: {csv_df['slot'].nunique()}")
    print(f"   Pitches: {csv_df['pitch_id'].nunique()}")

    print("\n   Sample matches:")
    for idx in [0, 50, 100, 150]:
        if idx < len(csv_df):
            row = csv_df.iloc[idx]
            print(f"   - {row['age_group']}: {row['team1']} vs {row['team2']} at {row['pitch_name']} ({row['time_label']})")
