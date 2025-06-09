import pandas as pd
from collections import defaultdict
import os
from datetime import datetime

def normalize_team_name(team_name, age_group=None):
    """Normalize team names for comparison"""
    team = team_name.strip().upper()
    
    # Remove age group suffix if present (for 2024 data)
    age_suffixes = [' U7', ' U8', ' U10', ' U12', ' U14']
    for suffix in age_suffixes:
        if team.endswith(suffix):
            team = team[:-len(suffix)]
            break
    
    return team

def extract_time_only(time_str):
    """Extract just the time portion from datetime string"""
    if pd.isna(time_str):
        return None
    
    # Handle different time formats
    time_str = str(time_str).strip()
    
    # If it's a full datetime, extract time
    if ' ' in time_str:
        return time_str.split(' ')[1]
    
    # If it's already just time
    return time_str

def remap_2024_pitch(pitch):
    """Remap 2024 pitches to 2025 field equivalents"""
    pitch_mapping = {
        'JP1.2': 'JP1.3',
        'JP1.3': 'JP1.4', 
        'JP2.4': 'JP4.3',
        'JP1.4': 'JP1.2'
    }
    
    return pitch_mapping.get(pitch, pitch)  # Return original if no mapping found

def ensure_output_dir():
    """Ensure data_out directory exists"""
    os.makedirs('data_out', exist_ok=True)

def load_2024_fixtures():
    """Load all 2024 fixture files"""
    fixtures_2024 = {}
    age_groups = ['u7', 'u8', 'u10', 'u12', 'u14']
    
    for age in age_groups:
        filename = f'data_in/mwc_2025_teams_u14 - 2024_scoresheet{age}.tsv'
        print(f"Loading 2024 fixtures: {filename}")
        
        try:
            df = pd.read_csv(filename, sep='\t')
            fixtures_list = []
            
            for _, row in df.iterrows():
                original_pitch = str(row['Pitch']).strip() if pd.notna(row['Pitch']) else ''
                remapped_pitch = remap_2024_pitch(original_pitch)
                
                fixture = {
                    'time': extract_time_only(row['Time']),
                    'pitch': remapped_pitch,  # Use remapped pitch for comparison
                    'team1': normalize_team_name(str(row['Team1'])),
                    'team2': normalize_team_name(str(row['Team2'])),
                    'original_time': str(row['Time']),
                    'original_team1': str(row['Team1']),
                    'original_team2': str(row['Team2']),
                    'original_pitch': original_pitch  # Keep original for reporting
                }
                fixtures_list.append(fixture)
            
            fixtures_2024[age.upper()] = fixtures_list
            print(f"  Loaded {len(fixtures_list)} fixtures for {age.upper()}")
            
        except FileNotFoundError:
            print(f"  WARNING: File {filename} not found!")
            fixtures_2024[age.upper()] = []
        except Exception as e:
            print(f"  ERROR loading {filename}: {e}")
            fixtures_2024[age.upper()] = []
    
    return fixtures_2024

def load_2025_fixtures():
    """Load 2025 fixtures file"""
    filename = 'data_in/mwc_2025_teams_u14 - app_fixtures.tsv'
    print(f"Loading 2025 fixtures: {filename}")
    
    try:
        df = pd.read_csv(filename, sep='\t')
        fixtures_2025 = defaultdict(list)
        
        for _, row in df.iterrows():
            age_group = str(row['Division']).strip().upper()
            
            fixture = {
                'time': extract_time_only(row['Starting time']),
                'field': str(row['Playing field']).strip() if pd.notna(row['Playing field']) else '',
                'team1': normalize_team_name(str(row['Team 1'])),
                'team2': normalize_team_name(str(row['Team 2'])),
                'day': str(row['Day']) if pd.notna(row['Day']) else '',
                'original_time': str(row['Starting time']),
                'original_team1': str(row['Team 1']),
                'original_team2': str(row['Team 2'])
            }
            fixtures_2025[age_group].append(fixture)
        
        total_fixtures = sum(len(fixtures) for fixtures in fixtures_2025.values())
        print(f"  Loaded {total_fixtures} total fixtures across all age groups")
        
        for age, fixtures in fixtures_2025.items():
            print(f"    {age}: {len(fixtures)} fixtures")
        
        return dict(fixtures_2025)
        
    except FileNotFoundError:
        print(f"  ERROR: File {filename} not found!")
        return {}
    except Exception as e:
        print(f"  ERROR loading {filename}: {e}")
        return {}

def create_fixture_key(fixture):
    """Create a unique key for fixture matching"""
    return f"{fixture['time']}_{fixture['team1']}_{fixture['team2']}"

def generate_markdown_report(results, fixtures_2024, fixtures_2025):
    """Generate comprehensive markdown report"""
    ensure_output_dir()
    
    report_path = f'data_out/fixtures_comparison_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("# 2024 vs 2025 Fixtures Comparison Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Executive Summary
        total_matches = sum(r['matches'] for r in results.values())
        total_mismatches = sum(len(r['mismatches']) for r in results.values())
        total_2024 = sum(r['total_2024'] for r in results.values())
        total_2025 = sum(r['total_2025'] for r in results.values())
        
        f.write("## Executive Summary\n\n")
        f.write(f"- **Total 2024 fixtures:** {total_2024}\n")
        f.write(f"- **Total 2025 fixtures:** {total_2025}\n")
        f.write(f"- **Perfect matches:** {total_matches}\n")
        f.write(f"- **Pitch/field mismatches:** {total_mismatches}\n")
        f.write(f"- **Missing fixtures:** {total_2024 + total_2025 - 2 * total_matches - total_mismatches}\n\n")
        
        # Status assessment
        if total_matches == total_2024 == total_2025 and total_mismatches == 0:
            f.write("🎉 **STATUS: EXCELLENT** - All fixtures match perfectly between 2024 and 2025!\n\n")
        elif total_mismatches == 0:
            f.write("✅ **STATUS: GOOD** - All matching fixtures have correct times and pitches!\n\n")
        else:
            f.write(f"⚠️ **STATUS: ACTION NEEDED** - {total_mismatches} fixtures have pitch/field mismatches!\n\n")
        
        # Summary Table
        f.write("## Summary by Age Group\n\n")
        f.write("| Age | 2024 Fixtures | 2025 Fixtures | Perfect Matches | Pitch Mismatches | Status |\n")
        f.write("|-----|---------------|---------------|-----------------|------------------|--------|\n")
        
        age_groups = sorted(results.keys())
        for age in age_groups:
            r = results[age]
            if r['total_2024'] == 0 and r['total_2025'] == 0:
                status = "No fixtures"
            elif r['matches'] == r['total_2024'] == r['total_2025'] and len(r['mismatches']) == 0:
                status = "✅ Perfect match"
            elif len(r['mismatches']) > 0:
                status = "⚠️ Pitch mismatches"
            elif len(r['missing_2024']) > 0 or len(r['missing_2025']) > 0:
                status = "📅 Different fixtures"
            else:
                status = "Unknown"
            
            f.write(f"| {age} | {r['total_2024']} | {r['total_2025']} | {r['matches']} | {len(r['mismatches'])} | {status} |\n")
        
        f.write("\n")
        
        # Detailed Analysis by Age Group
        f.write("## Detailed Analysis by Age Group\n\n")
        
        for age in age_groups:
            r = results[age]
            
            if r['total_2024'] == 0 and r['total_2025'] == 0:
                continue
                
            f.write(f"### {age}\n\n")
            f.write(f"**2024 fixtures:** {r['total_2024']} | **2025 fixtures:** {r['total_2025']} | **Perfect matches:** {r['matches']}\n\n")
            
            # Perfect match check
            if r['matches'] == r['total_2024'] == r['total_2025'] and len(r['mismatches']) == 0:
                f.write(f"✅ **PERFECT MATCH:** All {r['matches']} fixtures match perfectly!\n\n")
                continue
            
            # Pitch/field mismatches
            if r['mismatches']:
                f.write(f"#### ⚠️ Pitch/Field Mismatches ({len(r['mismatches'])})\n\n")
                f.write("| Time | Teams | 2024 Pitch | 2025 Field | Issue |\n")
                f.write("|------|-------|------------|------------|---------|\n")
                
                for mismatch in r['mismatches']:
                    f2024, f2025 = mismatch['f2024'], mismatch['f2025']
                    original_pitch = f2024.get('original_pitch', f2024['pitch'])
                    f.write(f"| {f2024['time']} | {f2024['team1']} vs {f2024['team2']} | {original_pitch} → {f2024['pitch']} | {f2025['field']} | Pitch mismatch |\n")
                f.write("\n")
            
            # Fixtures only in 2024
            if r['missing_2025']:
                f.write(f"#### 📅 Only in 2024 ({len(r['missing_2025'])})\n\n")
                f.write("| Time | Teams | Pitch |\n")
                f.write("|------|-------|-------|\n")
                
                for fixture in r['missing_2025']:
                    original_pitch = fixture.get('original_pitch', fixture['pitch'])
                    f.write(f"| {fixture['time']} | {fixture['team1']} vs {fixture['team2']} | {original_pitch} → {fixture['pitch']} |\n")
                f.write("\n")
            
            # Fixtures only in 2025
            if r['missing_2024']:
                f.write(f"#### 📅 Only in 2025 ({len(r['missing_2024'])})\n\n")
                f.write("| Time | Teams | Field | Day |\n")
                f.write("|------|-------|-------|-----|\n")
                
                for fixture in r['missing_2024']:
                    day = fixture.get('day', 'N/A')
                    f.write(f"| {fixture['time']} | {fixture['team1']} vs {fixture['team2']} | {fixture['field']} | {day} |\n")
                f.write("\n")
        
        # All Mismatches Summary
        if total_mismatches > 0:
            f.write("## All Pitch/Field Mismatches Summary\n\n")
            f.write("| Age | Time | Teams | 2024 Original → Remapped | 2025 Field |\n")
            f.write("|-----|------|-------|--------------------------|------------|\n")
            
            for age in age_groups:
                r = results[age]
                for mismatch in r['mismatches']:
                    f2024, f2025 = mismatch['f2024'], mismatch['f2025']
                    original_pitch = f2024.get('original_pitch', f2024['pitch'])
                    f.write(f"| {age} | {f2024['time']} | {f2024['team1']} vs {f2024['team2']} | {original_pitch} → {f2024['pitch']} | {f2025['field']} |\n")
            f.write("\n")
        
        # Data Sources
        f.write("## Data Sources\n\n")
        f.write("### 2024 Fixture Files (with pitch remapping)\n")
        f.write("**Pitch Remapping Applied:**\n")
        f.write("- JP1.2 → JP1.3\n")
        f.write("- JP1.3 → JP1.4\n") 
        f.write("- JP2.4 → JP4.3\n")
        f.write("- JP1.4 → JP1.2\n\n")
        
        for age in ['U7', 'U8', 'U10', 'U12', 'U14']:
            fixture_count = len(fixtures_2024.get(age, []))
            status = "✅ Loaded" if fixture_count > 0 else "❌ Missing"
            f.write(f"- `2024_scoresheet{age.lower()}.tsv`: {fixture_count} fixtures ({status})\n")
        
        f.write("\n### 2025 Fixture File\n")
        total_2025_all = sum(len(fixtures) for fixtures in fixtures_2025.values())
        f.write(f"- `app_fixtures.tsv`: {total_2025_all} fixtures across all age groups\n\n")
        
        # Recommendations
        f.write("## Recommendations\n\n")
        
        if total_mismatches > 0:
            f.write("### High Priority\n")
            f.write(f"1. **Fix {total_mismatches} pitch/field mismatches** - These need immediate attention to ensure proper venue assignments\n")
            f.write("2. **Review venue availability** - Confirm all assigned pitches/fields are available\n\n")
        
        missing_fixtures = total_2024 + total_2025 - 2 * total_matches - total_mismatches
        if missing_fixtures > 0:
            f.write("### Medium Priority\n")
            f.write(f"3. **Review {missing_fixtures} unmatched fixtures** - These may be new additions or cancellations\n")
            f.write("4. **Verify tournament structure** - Ensure the fixture format changes are intentional\n\n")
        
        f.write("### General\n")
        f.write("5. **Update 2025 fixtures** - Ensure all pitch assignments match the 2024 tested configuration\n")
        f.write("6. **Cross-reference with venue bookings** - Confirm all assigned venues are properly booked\n")
        f.write("7. **Coordinate with teams** - Notify teams of any fixture changes from 2024\n\n")
        
        # Footer
        f.write("---\n")
        f.write("*Report generated by fixtures comparison script*\n")
    
    print(f"\n📄 Markdown report saved to: {report_path}")
    return report_path

def compare_fixtures_for_age(age, fixtures_2024, fixtures_2025):
    """Compare fixtures for a specific age group"""
    print(f"\n" + "=" * 60)
    print(f"{age} FIXTURES COMPARISON")
    print("=" * 60)
    
    if not fixtures_2024 and not fixtures_2025:
        print("No fixtures found for this age group in either year.")
        return {'matches': 0, 'mismatches': [], 'missing_2024': [], 'missing_2025': [], 'total_2024': 0, 'total_2025': 0}
    
    if not fixtures_2024:
        print(f"No 2024 fixtures found, but {len(fixtures_2025)} 2025 fixtures exist.")
        return {'matches': 0, 'mismatches': [], 'missing_2024': fixtures_2025, 'missing_2025': [], 'total_2024': 0, 'total_2025': len(fixtures_2025)}
    
    if not fixtures_2025:
        print(f"No 2025 fixtures found, but {len(fixtures_2024)} 2024 fixtures exist.")
        return {'matches': 0, 'mismatches': [], 'missing_2024': [], 'missing_2025': fixtures_2024, 'total_2024': len(fixtures_2024), 'total_2025': 0}
    
    print(f"2024 fixtures: {len(fixtures_2024)}")
    print(f"2025 fixtures: {len(fixtures_2025)}")
    
    # Create lookup dictionaries
    fixtures_2024_dict = {create_fixture_key(f): f for f in fixtures_2024}
    fixtures_2025_dict = {create_fixture_key(f): f for f in fixtures_2025}
    
    # Find matches and mismatches
    matches = 0
    mismatches = []
    perfect_matches = []
    
    for key, f2024 in fixtures_2024_dict.items():
        if key in fixtures_2025_dict:
            f2025 = fixtures_2025_dict[key]
            
            # Check if pitch/field matches
            pitch_match = f2024['pitch'] == f2025['field']
            
            if pitch_match:
                matches += 1
                perfect_matches.append((f2024, f2025))
            else:
                mismatches.append({
                    'fixture_key': key,
                    'f2024': f2024,
                    'f2025': f2025,
                    'issue': 'pitch_mismatch'
                })
    
    # Find fixtures only in one year
    keys_2024 = set(fixtures_2024_dict.keys())
    keys_2025 = set(fixtures_2025_dict.keys())
    
    only_2024 = [fixtures_2024_dict[key] for key in keys_2024 - keys_2025]
    only_2025 = [fixtures_2025_dict[key] for key in keys_2025 - keys_2024]
    
    # Report results
    if matches == len(fixtures_2024) == len(fixtures_2025) and len(mismatches) == 0:
        print(f"✅ PERFECT MATCH: All {matches} fixtures match perfectly!")
    else:
        print(f"✅ Perfect matches: {matches}")
        
        if mismatches:
            print(f"⚠️  Pitch/field mismatches: {len(mismatches)}")
            for mismatch in mismatches[:5]:  # Show first 5
                f2024, f2025 = mismatch['f2024'], mismatch['f2025']
                original_pitch = f2024.get('original_pitch', f2024['pitch'])
                print(f"  {f2024['time']} {f2024['team1']} vs {f2024['team2']}")
                print(f"    2024 pitch: {original_pitch} → {f2024['pitch']} | 2025 field: {f2025['field']}")
            
            if len(mismatches) > 5:
                print(f"    ... and {len(mismatches) - 5} more")
        
        if only_2024:
            print(f"📅 Only in 2024: {len(only_2024)} fixtures")
            for fixture in only_2024[:3]:  # Show first 3
                original_pitch = fixture.get('original_pitch', fixture['pitch'])
                print(f"  {fixture['time']} {fixture['team1']} vs {fixture['team2']} @ {original_pitch} → {fixture['pitch']}")
            if len(only_2024) > 3:
                print(f"    ... and {len(only_2024) - 3} more")
        
        if only_2025:
            print(f"📅 Only in 2025: {len(only_2025)} fixtures")
            for fixture in only_2025[:3]:  # Show first 3
                print(f"  {fixture['time']} {fixture['team1']} vs {fixture['team2']} @ {fixture['field']}")
            if len(only_2025) > 3:
                print(f"    ... and {len(only_2025) - 3} more")
    
    return {
        'matches': matches,
        'mismatches': mismatches,
        'missing_2024': only_2025,
        'missing_2025': only_2024,
        'total_2024': len(fixtures_2024),
        'total_2025': len(fixtures_2025)
    }


# Main execution
print("=" * 80)
print("2024 vs 2025 FIXTURES COMPARISON (WITH PITCH REMAPPING)")
print("=" * 80)
print("Applying 2024 pitch remapping:")
print("  JP1.2 → JP1.3")
print("  JP1.3 → JP1.4") 
print("  JP2.4 → JP4.3")
print("  JP1.4 → JP1.2")
print("=" * 80)

# Load data
fixtures_2024 = load_2024_fixtures()
fixtures_2025 = load_2025_fixtures()

# Get all age groups from both datasets
all_ages = set(fixtures_2024.keys()) | set(fixtures_2025.keys())
age_groups = sorted(all_ages)

print(f"\nAge groups to compare: {', '.join(age_groups)}")

# Compare each age group
results = {}
for age in age_groups:
    f2024 = fixtures_2024.get(age, [])
    f2025 = fixtures_2025.get(age, [])
    results[age] = compare_fixtures_for_age(age, f2024, f2025)

# Generate markdown report
report_path = generate_markdown_report(results, fixtures_2024, fixtures_2025)

# Overall summary
print(f"\n" + "=" * 80)
print("OVERALL SUMMARY")
print("=" * 80)

total_matches = sum(r['matches'] for r in results.values())
total_mismatches = sum(len(r['mismatches']) for r in results.values())
total_2024 = sum(r['total_2024'] for r in results.values())
total_2025 = sum(r['total_2025'] for r in results.values())

print(f"Total fixtures comparison:")
print(f"  2024 fixtures: {total_2024}")
print(f"  2025 fixtures: {total_2025}")
print(f"  Perfect matches: {total_matches}")
print(f"  Pitch/field mismatches: {total_mismatches}")

# Summary table
print(f"\nSUMMARY BY AGE GROUP:")
print("-" * 70)
print(f"{'Age':<4} {'2024':<6} {'2025':<6} {'Match':<6} {'Mismatch':<9} {'Status':<20}")
print("-" * 70)

for age in age_groups:
    r = results[age]
    if r['total_2024'] == 0 and r['total_2025'] == 0:
        status = "No fixtures"
    elif r['matches'] == r['total_2024'] == r['total_2025'] and len(r['mismatches']) == 0:
        status = "✅ Perfect match"
    elif len(r['mismatches']) > 0:
        status = "⚠️ Pitch mismatches"
    elif len(r['missing_2024']) > 0 or len(r['missing_2025']) > 0:
        status = "📅 Different fixtures"
    else:
        status = "Unknown"
    
    print(f"{age:<4} {r['total_2024']:<6} {r['total_2025']:<6} {r['matches']:<6} {len(r['mismatches']):<9} {status:<20}")

# Final assessment
perfect_age_groups = sum(1 for r in results.values() 
                        if r['matches'] == r['total_2024'] == r['total_2025'] 
                        and len(r['mismatches']) == 0 
                        and r['total_2024'] > 0)

print(f"\n🎯 FINAL ASSESSMENT:")
print(f"Age groups with perfect fixture matches: {perfect_age_groups}/{len([r for r in results.values() if r['total_2024'] > 0 or r['total_2025'] > 0])}")

if total_matches == total_2024 == total_2025 and total_mismatches == 0:
    print("🎉 EXCELLENT: All fixtures match perfectly between 2024 and 2025!")
elif total_mismatches == 0:
    print("✅ GOOD: All matching fixtures have correct times and pitches!")
else:
    print(f"⚠️ ACTION NEEDED: {total_mismatches} fixtures have pitch/field mismatches!")

print(f"\n📄 Detailed report saved to: {report_path}")