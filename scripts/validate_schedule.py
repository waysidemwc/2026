import csv
import sys
from collections import defaultdict

def validate_csv(filename):
    print(f"--- Validating Schedule: {filename} ---")
    
    try:
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return

    # 1. Physical Constraints Checks
    slot_pitch_occupancy = defaultdict(list) # (slot, pitch_id) -> match
    team_slot_occupancy = defaultdict(list)   # (slot, team_name) -> match
    
    # 2. Logic / Rest Checks
    team_last_slot = {} # team -> last slot played
    team_rest_intervals = defaultdict(list) # team -> [list of slots between games]
    team_match_counts = defaultdict(int) # team -> count
    age_group_teams = defaultdict(set) # age -> {teams}
    age_group_pitches = defaultdict(set) # age -> {pitches}

    errors = []
    
    for row in data:
        slot = int(row['slot'])
        pitch = row['pitch_id']
        age = row['age_group']
        t1 = f"{age}:{row['team1']}"
        t2 = f"{age}:{row['team2']}"
        
        # Track age group sets
        age_group_teams[age].add(t1)
        age_group_teams[age].add(t2)
        age_group_pitches[age].add(pitch)
        
        # Pitch Double Booking Check
        if pitch in slot_pitch_occupancy[slot]:
            errors.append(f"Clash: Pitch {pitch} booked twice in Slot {slot}")
        slot_pitch_occupancy[slot].append(pitch)
        
        # Team Clash Check (Playing twice in one slot)
        for team in [t1, t2]:
            if team in team_slot_occupancy[slot]:
                errors.append(f"Clash: Team {team} scheduled twice in Slot {slot}")
            team_slot_occupancy[slot].append(team)
            team_match_counts[team] += 1
            
            # Rest Interval Check
            if team in team_last_slot:
                interval = slot - team_last_slot[team]
                if interval <= 0:
                    errors.append(f"Logic Error: Team {team} played in slot {slot} but last played in {team_last_slot[team]}")
                team_rest_intervals[team].append(interval)
            
            team_last_slot[team] = slot

    # --- Summary Report ---
    
    print(f"\n1. Global Integrity Check:")
    if not errors:
        print("   [OK] No Team Clashes.")
        print("   [OK] No Pitch Double-Bookings.")
    else:
        for err in errors:
            print(f"   [FAIL] {err}")

    print(f"\n2. Round Robin Completeness:")
    all_correct_rr = True
    for age, teams in age_group_teams.items():
        n = len(teams)
        expected_matches = n - 1
        for t in teams:
            if team_match_counts[t] != expected_matches:
                print(f"   [WARN] Team {t} played {team_match_counts[t]} matches. Expected {expected_matches}")
                all_correct_rr = False
    if all_correct_rr:
        print(f"   [OK] All teams play exactly N-1 matches.")

    print(f"\n3. Rest / Spacing Analysis:")
    min_rest = 999
    consecutive_games = 0
    for team, intervals in team_rest_intervals.items():
        for interval in intervals:
            # We care about rest relative to slots. interval=1 means consecutive.
            if interval == 1:
                consecutive_games += 1
            min_rest = min(min_rest, interval)
            
    if min_rest > 1:
        print(f"   [EXCELLENT] No consecutive games! Minimum rest is {min_rest-1} slot(s).")
    else:
        print(f"   [WARN] There are {consecutive_games} instances of teams playing back-to-back games.")

    print(f"\n4. Zone / Pitch Ring-Fencing:")
    for age, pitches in age_group_pitches.items():
        print(f"   - {age}: Uses {len(pitches)} pitch(es) ({', '.join(sorted(pitches))})")

if __name__ == "__main__":
    target = "master_schedule_final.csv"
    if len(sys.argv) > 1:
        target = sys.argv[1]
    validate_csv(target)
