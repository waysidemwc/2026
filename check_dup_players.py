import pandas as pd
from collections import Counter, defaultdict

# 1. Load the TSV
file_path = 'data_in/mwc_2025_teams_export.tsv'  # adjust path if needed
df = pd.read_csv(file_path, sep='\t')

# 2. Create a list to store all player records with their metadata
all_player_records = []

# Process each row to extract players with their age, country info
for _, row in df.iterrows():
    age = row['Age']
    country_name = row['Name'] 
    country_code = row['Country']
    players_str = row['Players']
    
    if pd.notna(players_str):  # Check if players field is not empty
        # Split players by comma and clean whitespace
        players = [name.strip() for name in players_str.split(',') if name.strip()]
        
        # Add each player with their metadata
        for player in players:
            all_player_records.append({
                'player_name': player,
                'age': age,
                'country_name': country_name,
                'country_code': country_code
            })

# 3. Find duplicate players
player_name_counts = Counter([record['player_name'] for record in all_player_records])
duplicates = {name: count for name, count in player_name_counts.items() if count > 1}

# 4. Group duplicate player records
duplicate_records = defaultdict(list)
for record in all_player_records:
    if record['player_name'] in duplicates:
        duplicate_records[record['player_name']].append(record)

# 5. Report duplicates
print("=" * 60)
print("DUPLICATE PLAYERS ANALYSIS")
print("=" * 60)

if duplicates:
    print(f"Found {len(duplicates)} players with duplicate names:\n")
    
    for player_name in sorted(duplicates.keys()):
        count = duplicates[player_name]
        print(f"Player: {player_name} (appears {count} times)")
        
        records = duplicate_records[player_name]
        for i, record in enumerate(records, 1):
            print(f"  {i}. Age: {record['age']}, Country: {record['country_name']} ({record['country_code']})")
        print()
else:
    print("No duplicate player names found.\n")

# 6. Count players per age group
print("=" * 60)
print("PLAYERS COUNT BY AGE GROUP")
print("=" * 60)

age_counts = Counter([record['age'] for record in all_player_records])
total_players = len(all_player_records)

for age in sorted(age_counts.keys()):
    count = age_counts[age]
    print(f"{age}: {count} players")

print(f"\nTotal players across all age groups: {total_players}")

# 7. Count players per Age-Country combination
print("\n" + "=" * 60)
print("PLAYERS COUNT BY AGE-COUNTRY COMBINATION")
print("=" * 60)

age_country_counts = Counter([(record['age'], record['country_name']) for record in all_player_records])

# Sort by age first, then by country
for (age, country) in sorted(age_country_counts.keys()):
    count = age_country_counts[(age, country)]
    print(f"{age}-{country}: {count} players")

# 8. Additional summary statistics
print("\n" + "=" * 60)
print("SUMMARY STATISTICS")
print("=" * 60)

#country_counts = Counter([record['country_name'] for record in all_player_records])
#print("Total players by country:")
#for country in sorted(country_counts.keys()):
#    count = country_counts[country]
#    print(f"  {country}: {count} players")

print(f"\nUnique player names: {len(set([record['player_name'] for record in all_player_records]))}")
print(f"Total player entries: {total_players}")
print(f"Duplicate names: {len(duplicates)}")
print(f"Players with duplicate names: {sum(duplicates.values())}")