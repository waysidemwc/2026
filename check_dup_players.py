import pandas as pd
from collections import Counter

# 1. Load the TSV
file_path = 'data_in/mwc_2025_teams_export.tsv'  # adjust path if needed
df = pd.read_csv(file_path, sep='\t', usecols=['Players'])

# 2. Split and strip
#    If your delimiter is something else, change ',' to that.
players_series = df['Players'].dropna().apply(
    lambda cell: [name.strip() for name in cell.split(',')]
)

# 3. Flatten into one list
all_players = [name for sublist in players_series for name in sublist]

# 4. Count and filter duplicates
counts = Counter(all_players)
duplicates = {name: cnt for name, cnt in counts.items() if cnt > 1}

# Report
if duplicates:
    print("Duplicate player names found:")
    for name, cnt in duplicates.items():
        print(f"  {name}: {cnt} times")
else:
    print("No duplicate player names found.")
