import pandas as pd
from collections import Counter, defaultdict

def normalize_name(name):
    """Normalize names for comparison - remove extra spaces, convert to uppercase"""
    return ' '.join(name.strip().upper().split())

def load_teams_data(teams_file):
    """Load and organize teams data by age group"""
    print(f"Loading teams file: {teams_file}")
    df_teams = pd.read_csv(teams_file, sep='\t')
    
    teams_data = defaultdict(list)
    
    for _, row in df_teams.iterrows():
        age = row['Age']
        players_str = row['Players']
        
        if pd.notna(players_str):
            players = [name.strip() for name in players_str.split(',') if name.strip()]
            for player in players:
                teams_data[age].append({
                    'name': normalize_name(player),
                    'original_name': player,
                    'country': row['Name']
                })
    
    return teams_data

def load_registration_data(reg_file, age_group):
    """Load registration data for specific age group"""
    print(f"Loading registration file: {reg_file}")
    try:
        df_reg = pd.read_csv(reg_file, sep='\t')
        
        reg_players = []
        for _, row in df_reg.iterrows():
            if pd.notna(row['First Name Last Name']):
                full_name = row['First Name Last Name'].strip()
                reg_players.append({
                    'name': normalize_name(full_name),
                    'original_name': full_name,
                    'team': row.get('Team #', 'N/A'),
                    'dob': row.get('DOB', 'N/A'),
                    'gender': row.get('Gender', 'N/A'),
                    'country': row.get('Country', 'N/A')
                })
        
        return reg_players
    except FileNotFoundError:
        print(f"WARNING: File {reg_file} not found!")
        return []
    except Exception as e:
        print(f"ERROR loading {reg_file}: {e}")
        return []

def compare_age_group(age, teams_players, reg_players):
    """Compare players for a specific age group"""
    teams_names = set([player['name'] for player in teams_players])
    reg_names = set([player['name'] for player in reg_players])
    
    matches = teams_names.intersection(reg_names)
    only_in_teams = teams_names - reg_names
    only_in_registration = reg_names - teams_names
    
    # Check country assignments for matching players
    country_mismatches = []
    country_mapping = {
        'ARGENTINA': 'AR', 'BRAZIL': 'BR', 'ENGLAND': 'GBENG', 'FRANCE': 'FR',
        'GERMANY': 'DE', 'HOLLAND': 'NL', 'IRELAND': 'IE', 'ITALY': 'IT',
        'PORTUGAL': 'PT', 'SPAIN': 'ES'
    }
    
    for name in matches:
        # Get team assignment (country from teams file)
        team_player = next((p for p in teams_players if p['name'] == name), None)
        # Get registration country
        reg_player = next((p for p in reg_players if p['name'] == name), None)
        
        if team_player and reg_player:
            team_country = team_player['country']
            reg_country = reg_player.get('country', 'N/A')
            
            # Normalize country names for comparison
            if reg_country != 'N/A' and team_country != reg_country:
                country_mismatches.append({
                    'name': name,
                    'original_name': team_player['original_name'],
                    'team_country': team_country,
                    'reg_country': reg_country
                })
    
    return {
        'age': age,
        'teams_count': len(teams_names),
        'reg_count': len(reg_names),
        'matches': matches,
        'only_in_teams': only_in_teams,
        'only_in_registration': only_in_registration,
        'teams_players': teams_players,
        'reg_players': reg_players,
        'country_mismatches': country_mismatches
    }

# Configuration
age_groups = ['U7', 'U8', 'U10', 'U12', 'U14']
registration_files = {
    'U7': 'data_in/mwc_2025_teams_u14 - MattSheetu7.tsv',
    'U8': 'data_in/mwc_2025_teams_u14 - MattSheetu8.tsv',
    'U10': 'data_in/mwc_2025_teams_u14 - MattSheetu10.tsv',
    'U12': 'data_in/mwc_2025_teams_u14 - MattSheetu12.tsv',
    'U14': 'data_in/mwc_2025_teams_u14 - MattSheetu14.tsv'
}

# Load teams data
teams_data = load_teams_data('data_in/mwc_2025_teams_export.tsv')

# Load registration data for each age group
registration_data = {}
for age in age_groups:
    if age in registration_files:
        registration_data[age] = load_registration_data(registration_files[age], age)
    else:
        registration_data[age] = []

# Compare each age group
comparisons = {}
for age in age_groups:
    teams_players = teams_data.get(age, [])
    reg_players = registration_data.get(age, [])
    comparisons[age] = compare_age_group(age, teams_players, reg_players)

# Generate comprehensive report
print("\n" + "=" * 100)
print("MULTI-AGE GROUP COMPARISON REPORT")
print("=" * 100)

# Summary table
print("\nSUMMARY TABLE:")
print("-" * 90)
print(f"{'Age':<4} {'Teams':<7} {'Reg':<7} {'Match':<7} {'Teams Only':<11} {'Reg Only':<9} {'Country Err':<11} {'Match %':<8}")
print("-" * 90)

total_teams = 0
total_reg = 0
total_matches = 0
total_country_errors = 0

for age in age_groups:
    comp = comparisons[age]
    match_pct = (len(comp['matches']) / max(comp['teams_count'], comp['reg_count']) * 100) if max(comp['teams_count'], comp['reg_count']) > 0 else 0
    country_errors = len(comp['country_mismatches'])
    
    print(f"{age:<4} {comp['teams_count']:<7} {comp['reg_count']:<7} {len(comp['matches']):<7} {len(comp['only_in_teams']):<11} {len(comp['only_in_registration']):<9} {country_errors:<11} {match_pct:<7.1f}%")
    
    total_teams += comp['teams_count']
    total_reg += comp['reg_count']
    total_matches += len(comp['matches'])
    total_country_errors += country_errors

print("-" * 90)
overall_match_pct = (total_matches / max(total_teams, total_reg) * 100) if max(total_teams, total_reg) > 0 else 0
print(f"{'TOT':<4} {total_teams:<7} {total_reg:<7} {total_matches:<7} {'':<11} {'':<9} {total_country_errors:<11} {overall_match_pct:<7.1f}%")

# Detailed analysis for each age group
for age in age_groups:
    comp = comparisons[age]
    
    if comp['teams_count'] == 0 and comp['reg_count'] == 0:
        continue
        
    print(f"\n" + "=" * 60)
    print(f"{age} DETAILED ANALYSIS")
    print("=" * 60)
    
    # Perfect match check
    if len(comp['matches']) == comp['teams_count'] == comp['reg_count'] and comp['teams_count'] > 0 and len(comp['country_mismatches']) == 0:
        print(f"✅ PERFECT MATCH: All {comp['teams_count']} players match with correct countries!")
        continue
    
    # Show country mismatches first (most important)
    if comp['country_mismatches']:
        print(f"\n🚨 COUNTRY MISMATCHES ({len(comp['country_mismatches'])}):")
        for mismatch in comp['country_mismatches']:
            print(f"  ⚠️  {mismatch['original_name']}")
            print(f"      Team Assignment: {mismatch['team_country']}")
            print(f"      Registration:    {mismatch['reg_country']}")
            print()
    
    # Show mismatches
    if comp['only_in_teams']:
        print(f"\n🔍 ONLY IN TEAMS FILE ({len(comp['only_in_teams'])}):")
        for name in sorted(comp['only_in_teams']):
            original_name = next((p['original_name'] for p in comp['teams_players'] if p['name'] == name), name)
            country = next((p['country'] for p in comp['teams_players'] if p['name'] == name), 'N/A')
            print(f"  - {original_name} (Country: {country})")
    
    if comp['only_in_registration']:
        print(f"\n📋 ONLY IN REGISTRATION FILE ({len(comp['only_in_registration'])}):")
        for name in sorted(comp['only_in_registration']):
            reg_player = next((p for p in comp['reg_players'] if p['name'] == name), None)
            if reg_player:
                print(f"  + {reg_player['original_name']} (Team: {reg_player['team']})")
    
    # Check for duplicates in registration
    if comp['reg_players']:
        reg_name_counts = Counter([player['name'] for player in comp['reg_players']])
        duplicates = {name: count for name, count in reg_name_counts.items() if count > 1}
        
        if duplicates:
            print(f"\n⚠️  DUPLICATES IN REGISTRATION ({len(duplicates)}):")
            for name, count in duplicates.items():
                instances = [p for p in comp['reg_players'] if p['name'] == name]
                print(f"  {name} (appears {count} times):")
                for i, instance in enumerate(instances, 1):
                    print(f"    {i}. {instance['original_name']} (Team: {instance['team']})")

# Overall statistics
print(f"\n" + "=" * 60)
print("OVERALL STATISTICS")
print("=" * 60)

perfect_matches = sum(1 for age in age_groups if len(comparisons[age]['matches']) == comparisons[age]['teams_count'] == comparisons[age]['reg_count'] and comparisons[age]['teams_count'] > 0 and len(comparisons[age]['country_mismatches']) == 0)
age_groups_with_data = sum(1 for age in age_groups if comparisons[age]['teams_count'] > 0 or comparisons[age]['reg_count'] > 0)

print(f"Age groups analyzed: {age_groups_with_data}")
print(f"Perfect matches (names + countries): {perfect_matches}")
print(f"Age groups with discrepancies: {age_groups_with_data - perfect_matches}")
print(f"Total players in teams file: {total_teams}")
print(f"Total players in registration files: {total_reg}")
print(f"Total country assignment errors: {total_country_errors}")
print(f"Overall match rate: {overall_match_pct:.1f}%")

# Final status
if perfect_matches == age_groups_with_data and age_groups_with_data > 0:
    print("\n🎉 ALL AGE GROUPS HAVE PERFECT MATCHES!")
elif total_matches == max(total_teams, total_reg) and total_country_errors == 0:
    print("\n✅ COMPLETE MATCH: All players accounted for with correct countries!")
elif total_country_errors > 0:
    print(f"\n🚨 COUNTRY ASSIGNMENT ERRORS: {total_country_errors} players assigned to wrong countries!")
else:
    print(f"\n⚠️  DISCREPANCIES FOUND: {age_groups_with_data - perfect_matches} age groups have mismatches.")