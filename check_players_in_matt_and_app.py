import pandas as pd
from collections import Counter

def normalize_name(name):
    """Normalize names for comparison - remove extra spaces, convert to uppercase"""
    return ' '.join(name.strip().upper().split())

# 1. Load the main teams file and extract U14 players
print("Loading main teams file...")
teams_file = 'data_in/mwc_2025_teams_export.tsv'
df_teams = pd.read_csv(teams_file, sep='\t')

# Extract U14 players from main file
u14_teams_players = []
for _, row in df_teams.iterrows():
    if row['Age'] == 'U14':
        players_str = row['Players']
        if pd.notna(players_str):
            players = [name.strip() for name in players_str.split(',') if name.strip()]
            for player in players:
                u14_teams_players.append({
                    'name': normalize_name(player),
                    'original_name': player,
                    'country': row['Name']
                })

print(f"Found {len(u14_teams_players)} U14 players in teams file")

# 2. Load the U14 registration file
print("Loading U14 registration file...")
u14_reg_file = 'data_in/mwc_2025_teams_u14 - MattSheetu14.tsv'
df_u14_reg = pd.read_csv(u14_reg_file, sep='\t')

# Extract players from registration file
u14_reg_players = []
for _, row in df_u14_reg.iterrows():
    if pd.notna(row['First Name Last Name']):
        full_name = row['First Name Last Name'].strip()
        u14_reg_players.append({
            'name': normalize_name(full_name),
            'original_name': full_name,
            'team': row.get('Team #', 'N/A'),
            'dob': row.get('DOB', 'N/A'),
            'gender': row.get('Gender', 'N/A')
        })

print(f"Found {len(u14_reg_players)} U14 players in registration file")

# 3. Create sets for comparison
teams_names = set([player['name'] for player in u14_teams_players])
reg_names = set([player['name'] for player in u14_reg_players])

# 4. Find matches and differences
matches = teams_names.intersection(reg_names)
only_in_teams = teams_names - reg_names
only_in_registration = reg_names - teams_names

# 5. Report results
print("\n" + "=" * 80)
print("U14 PLAYERS COMPARISON REPORT")
print("=" * 80)

print(f"\nSUMMARY:")
print(f"Players in teams file: {len(teams_names)}")
print(f"Players in registration file: {len(reg_names)}")
print(f"Matching players: {len(matches)}")
print(f"Only in teams file: {len(only_in_teams)}")
print(f"Only in registration file: {len(only_in_registration)}")

# 6. Show matching players
if matches:
    print(f"\n" + "=" * 50)
    print(f"MATCHING PLAYERS ({len(matches)})")
    print("=" * 50)
    
    for name in sorted(matches):
        # Find original names from both files
        teams_original = next((p['original_name'] for p in u14_teams_players if p['name'] == name), name)
        reg_original = next((p['original_name'] for p in u14_reg_players if p['name'] == name), name)
        teams_country = next((p['country'] for p in u14_teams_players if p['name'] == name), 'N/A')
        
        print(f"✓ {teams_original}")
        if teams_original != reg_original:
            print(f"  (Registration: {reg_original})")
        print(f"  Country: {teams_country}")

# 7. Show players only in teams file
if only_in_teams:
    print(f"\n" + "=" * 50)
    print(f"ONLY IN TEAMS FILE ({len(only_in_teams)})")
    print("=" * 50)
    
    for name in sorted(only_in_teams):
        original_name = next((p['original_name'] for p in u14_teams_players if p['name'] == name), name)
        country = next((p['country'] for p in u14_teams_players if p['name'] == name), 'N/A')
        print(f"- {original_name} (Country: {country})")

# 8. Show players only in registration file
if only_in_registration:
    print(f"\n" + "=" * 50)
    print(f"ONLY IN REGISTRATION FILE ({len(only_in_registration)})")
    print("=" * 50)
    
    for name in sorted(only_in_registration):
        reg_player = next((p for p in u14_reg_players if p['name'] == name), None)
        if reg_player:
            print(f"+ {reg_player['original_name']}")
            print(f"  Team: {reg_player['team']}, DOB: {reg_player['dob']}, Gender: {reg_player['gender']}")

# 9. Check for potential duplicates in registration file
print(f"\n" + "=" * 50)
print("DUPLICATE CHECK IN REGISTRATION FILE")
print("=" * 50)

reg_name_counts = Counter([player['name'] for player in u14_reg_players])
duplicates_in_reg = {name: count for name, count in reg_name_counts.items() if count > 1}

if duplicates_in_reg:
    print(f"Found {len(duplicates_in_reg)} duplicate names in registration file:")
    for name, count in duplicates_in_reg.items():
        print(f"  {name}: appears {count} times")
        # Show all instances
        instances = [p for p in u14_reg_players if p['name'] == name]
        for i, instance in enumerate(instances, 1):
            print(f"    {i}. {instance['original_name']} (Team: {instance['team']})")
else:
    print("No duplicate names found in registration file.")

# 10. Final statistics
print(f"\n" + "=" * 50)
print("FINAL STATISTICS")
print("=" * 50)

match_percentage = (len(matches) / max(len(teams_names), len(reg_names))) * 100
print(f"Match rate: {match_percentage:.1f}%")
print(f"Total unique players across both files: {len(teams_names.union(reg_names))}")

if len(matches) == len(teams_names) == len(reg_names):
    print("✅ PERFECT MATCH: All players appear in both files!")
elif len(only_in_teams) == 0 and len(only_in_registration) == 0:
    print("✅ COMPLETE MATCH: Same players in both files!")
else:
    print("⚠️  DIFFERENCES FOUND: Files contain different player lists.")