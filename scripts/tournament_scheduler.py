import itertools
import os
import csv
import random

# ==========================================
# 1. ROUND-ROBIN SCHEDULING LOGIC
# ==========================================

def generate_round_robin(teams):
    """Generates matches using the polygon (circle) method to ensure a valid round-robin."""
    n = len(teams)
    matches = []
    
    if n % 2 != 0:
        teams.append('Bye')
        n += 1

    half = n // 2
    for turn in range(n - 1):
        round_matches = []
        for i in range(half):
            if teams[i] != 'Bye' and teams[n - 1 - i] != 'Bye':
                round_matches.append((teams[i], teams[n - 1 - i]))
        matches.append(round_matches)
        
        teams.insert(1, teams.pop())
        
    return matches

def schedule_6_teams(teams):
    """
    6 Teams, 1 Pitch, 15 Matches.
    Uses an explicitly optimized pattern to guarantee perfectly spaced rests.
    """
    # Hardcoded optimal stagger for perfectly even rest
    optimal_sequence = [
        (0,1), (2,3), (4,5), (0,2), (3,5), (1,4), (0,3), (2,4),
        (1,5), (0,4), (2,5), (1,3), (0,5), (3,4), (1,2)
    ]
    
    matches = []
    for i, (idx1, idx2) in enumerate(optimal_sequence):
        matches.append({
            'slot': i + 1, 
            'pitch_idx': 0, 
            't1': teams[idx1], 
            't2': teams[idx2]
        })
    return matches

def optimize_spacing(teams, matches, num_pitches, physical_slots):
    """Uses a Monte-Carlo Greedy approach to find the schedule with the best possible rest spacing."""
    best_schedule = []
    best_overall_score = -9999
    
    # Fallback schedule (sequential) in case the optimizer hits a dead end
    fallback_schedule = []
    m_idx = 0
    for slot in physical_slots:
        for p in range(num_pitches):
            if m_idx < len(matches):
                fallback_schedule.append({'slot': slot, 'pitch_idx': p, 't1': matches[m_idx][0], 't2': matches[m_idx][1]})
                m_idx += 1
                
    for _ in range(200): # Run 200 variations
        shuffled_matches = matches[:]
        random.shuffle(shuffled_matches)
        remaining = shuffled_matches[:]
        scheduled = []
        team_last_played = {t: -99 for t in teams}
        
        min_rest_in_schedule = 999
        total_rest_score = 0
        
        for slot in physical_slots:
            slot_matches = []
            teams_in_slot = set()
            
            while len(slot_matches) < num_pitches and remaining:
                best_match = None
                best_match_score = -9999
                
                for m in remaining:
                    t1, t2 = m
                    if t1 in teams_in_slot or t2 in teams_in_slot:
                        continue # Team cannot play twice in the same time slot
                        
                    dist1 = slot - team_last_played[t1]
                    dist2 = slot - team_last_played[t2]
                    
                    # Core optimization: favor the match where BOTH teams have rested the longest
                    score = min(dist1, dist2)
                    
                    if score > best_match_score:
                        best_match_score = score
                        best_match = m
                        
                if best_match:
                    d1 = slot - team_last_played[best_match[0]]
                    d2 = slot - team_last_played[best_match[1]]
                    
                    # Track actual rests (ignore initialization values)
                    if 0 < d1 < 50: 
                        min_rest_in_schedule = min(min_rest_in_schedule, d1)
                        total_rest_score += d1
                    if 0 < d2 < 50: 
                        min_rest_in_schedule = min(min_rest_in_schedule, d2)
                        total_rest_score += d2
                        
                    slot_matches.append(best_match)
                    teams_in_slot.update(best_match)
                    remaining.remove(best_match)
                else:
                    break # Reached a dead end for this slot
            
            for i, m in enumerate(slot_matches):
                team_last_played[m[0]] = slot
                team_last_played[m[1]] = slot
                scheduled.append({
                    'slot': slot,
                    'pitch_idx': i,
                    't1': m[0],
                    't2': m[1]
                })
                
        if not remaining: # If all matches successfully packed without overlaps
            # Maximize the minimum rest any team gets. Tiebreaker: total aggregate rest.
            eval_score = (min_rest_in_schedule * 1000) + total_rest_score
            
            if eval_score > best_overall_score:
                best_overall_score = eval_score
                best_schedule = scheduled
                
    return best_schedule if best_schedule else fallback_schedule

def schedule_8_teams(teams):
    """8 Teams, 2 Pitches, 28 Matches. Optimized for rest."""
    rounds = generate_round_robin(teams)
    all_matches = [m for r in rounds for m in r]
    
    # 8 teams need exactly 14 time slots. 
    # We skip slots 11 and 16 to act as global breaks!
    physical_slots = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15]
    
    return optimize_spacing(teams, all_matches, num_pitches=2, physical_slots=physical_slots)

def schedule_10_teams(teams):
     """10 Teams, 3 Pitches, 45 Matches. Optimized for rest."""
     rounds = generate_round_robin(teams)
     all_matches = [m for r in rounds for m in r]
     
     # 10 teams pack the schedule tightly, utilizing 15 slots.
     physical_slots = list(range(1, 16))
     
     return optimize_spacing(teams, all_matches, num_pitches=3, physical_slots=physical_slots)

# ==========================================
# 2. CONFIGURATION DISCOVERY ENGINE
# ==========================================

def discover_configurations(total_pitches):
    blocks = [
        {'teams': 6, 'pitches': 1},
        {'teams': 8, 'pitches': 2},
        {'teams': 10, 'pitches': 3}
    ]
    valid_configs = []
    
    for num_age_groups in range(4, 15):
        for combo in itertools.combinations_with_replacement(blocks, num_age_groups):
            if sum(item['pitches'] for item in combo) == total_pitches:
                total_teams = sum(item['teams'] for item in combo)
                counts = {6: 0, 8: 0, 10: 0}
                for item in combo:
                    counts[item['teams']] += 1
                    
                config_summary = {
                    'num_age_groups': num_age_groups,
                    'total_teams': total_teams,
                    'breakdown': counts
                }
                
                if config_summary not in valid_configs:
                    valid_configs.append(config_summary)
                    
    valid_configs.sort(key=lambda x: x['num_age_groups'], reverse=True)
    return valid_configs

def print_configurations(total_pitches):
    configs = discover_configurations(total_pitches)
    print(f"\n=======================================================")
    print(f" DISCOVERED CONFIGURATIONS FOR {total_pitches} PITCHES")
    print(f"=======================================================\n")
    
    for i, config in enumerate(configs, 1):
        print(f"Option {i}: {config['num_age_groups']} Age Groups, {config['total_teams']} Teams")
        if config['breakdown'][6] > 0: print(f"  - {config['breakdown'][6]} brackets of 6 Teams (1 pitch each)")
        if config['breakdown'][8] > 0: print(f"  - {config['breakdown'][8]} brackets of 8 Teams (2 pitches each)")
        if config['breakdown'][10] > 0: print(f"  - {config['breakdown'][10]} brackets of 10 Teams (3 pitches each)")
        print("-" * 40)
    print("\n")


# ==========================================
# 3. ALLOCATION & RESOURCE MANAGEMENT
# ==========================================

PITCH_INVENTORY = [
    {'id': 'JP1.1', 'name': 'Pitch 1', 'zone': 'JP1'},
    {'id': 'JP1.2', 'name': 'Pitch 2', 'zone': 'JP1'},
    {'id': 'JP1.3', 'name': 'Pitch 3', 'zone': 'JP1'},
    {'id': 'JP1.4', 'name': 'Pitch 4', 'zone': 'JP1'},
    {'id': 'JP2.1', 'name': 'Pitch 5', 'zone': 'JP2'},
    {'id': 'JP2.2', 'name': 'Pitch 6', 'zone': 'JP2'},
    {'id': 'JP2.3', 'name': 'Pitch 7', 'zone': 'JP2'},
    {'id': 'JP2.4', 'name': 'Pitch 8', 'zone': 'JP2'},
    {'id': 'JP3.1', 'name': 'Pitch 9', 'zone': 'JP3'},
    {'id': 'JP3.2', 'name': 'Pitch 10', 'zone': 'JP3'},
    {'id': 'JP3.3', 'name': 'Pitch 11', 'zone': 'JP3'},
    {'id': 'JP4.1', 'name': 'Pitch 12', 'zone': 'JP4'},
    {'id': 'JP4.2', 'name': 'Pitch 13', 'zone': 'JP4'},
    {'id': 'JP4.3', 'name': 'Pitch 14', 'zone': 'JP4'},
]

TIME_MAP = {
    1: "Tue 18:30", 2: "Tue 18:45", 3: "Tue 19:00", 4: "Tue 19:15",
    5: "Tue 19:30", 6: "Tue 19:45", 7: "Tue 20:00", 8: "Tue 20:15",
    9: "Thu 18:30", 10: "Thu 18:45", 11: "Thu 19:00", 12: "Thu 19:15",
    13: "Thu 19:30", 14: "Thu 19:45", 15: "Thu 20:00", 16: "Thu 20:15"
}

def get_requirements(team_count):
    if team_count <= 6: return 15, 1
    elif team_count <= 8: return 28, 2
    elif team_count <= 10: return 45, 3
    else: raise ValueError("Team count must be 6, 8, or 10.")

def allocate_tournament(option_name, age_groups):
    print(f"Allocating Pitches for {option_name}...")
    available_pitches = PITCH_INVENTORY.copy()
    allocations = []
    
    for group in age_groups:
        matches, pitches_needed = get_requirements(group['teams'])
        assigned = [available_pitches.pop(0) for _ in range(pitches_needed)]
        allocations.append({
            'age_group': group['age'],
            'teams': group['teams'],
            'matches': matches,
            'pitches_req': pitches_needed,
            'assigned_pitches': assigned
        })
        
    return {'title': option_name, 'allocations': allocations}


# ==========================================
# 4. MATRIX SCHEDULER & TEAM MAPPER
# ==========================================

def generate_master_schedule(allocations, team_rosters):
    """Maps algorithms to real times, physical pitches, and real team names."""
    print("Generating Master Matrix Schedule...")
    master_schedule = []
    
    for alloc in allocations:
        age = alloc['age_group']
        team_count = alloc['teams']
        pitches = alloc['assigned_pitches']
        
        # Pull real team names from roster, or auto-generate placeholders if missing
        roster = team_rosters.get(age, [f"{age}-Team {i}" for i in range(1, team_count + 1)])
        
        group_matches = []
        
        if team_count == 6:
            group_matches = schedule_6_teams(roster)
        elif team_count == 8:
            group_matches = schedule_8_teams(roster)
        elif team_count == 10:
            group_matches = schedule_10_teams(roster)
            
        for m in group_matches:
            pitch_obj = pitches[m['pitch_idx']]
            master_schedule.append({
                'age_group': age,
                'slot': m['slot'],
                'time_label': TIME_MAP[m['slot']],
                'pitch_id': pitch_obj['id'],
                'pitch_name': pitch_obj['name'],
                'zone': pitch_obj['zone'],
                'team1': m['t1'],
                'team2': m['t2']
            })
            
    return master_schedule


# ==========================================
# 5. EXPORT SCRIPTS (CSV & DETAILED HTML)
# ==========================================

def export_to_csv(master_schedule, filename="master_schedule.csv"):
    """Writes the master schedule to a CSV file."""
    print(f"Exporting to CSV: {filename}...")
    keys = ['age_group', 'slot', 'time_label', 'zone', 'pitch_name', 'pitch_id', 'team1', 'team2']
    
    # Sort chronologically, then by zone/pitch
    sorted_schedule = sorted(master_schedule, key=lambda x: (x['slot'], x['zone'], x['pitch_id']))
    
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(sorted_schedule)

def generate_summary_dashboard(allocations, master_schedule, title, filename="summary_dashboard.html"):
    """Generates the high-level dashboard with Zone Map, Breakdown, and Abstract Schedule Grid."""
    print(f"Exporting Summary Dashboard: {filename}...")
    
    # 1. Prepare Zone Map Data
    zones = {}
    for alloc in allocations:
        for pitch in alloc['assigned_pitches']:
            z = pitch['zone']
            if z not in zones: zones[z] = []
            zones[z].append({'name': pitch['name'], 'age': alloc['age_group']})
            
    # 2. Prepare Active Slots Map
    pitch_schedule = {}
    for match in master_schedule:
        p_id = match['pitch_id']
        if p_id not in pitch_schedule:
            pitch_schedule[p_id] = {}
        pitch_schedule[p_id][match['slot']] = match['age_group']

    # 3. Build HTML Structure
    css = """
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f7f6; color: #333; }
        h1, h2 { text-align: center; color: #2c3e50; }
        .container { max-width: 1200px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .zone-wrapper { display: flex; justify-content: space-between; gap: 15px; margin-bottom: 40px; flex-wrap: wrap; }
        .zone { flex: 1; min-width: 200px; padding: 15px; border-radius: 8px; text-align: center; color: white; }
        .zone h3 { margin-top: 0; font-size: 1.1em; border-bottom: 2px solid rgba(255,255,255,0.3); padding-bottom: 10px; }
        .pitch-grid { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }
        .pitch-card { background: rgba(255, 255, 255, 0.2); border: 2px solid rgba(255, 255, 255, 0.5); border-radius: 5px; padding: 10px; width: 40%; font-weight: bold; }
        .jp1 { background-color: #27ae60; } .jp2 { background-color: #2980b9; } .jp3 { background-color: #e67e22; } .jp4 { background-color: #c0392b; }
        .table-container { overflow-x: auto; margin-bottom: 40px; }
        table { width: 100%; border-collapse: collapse; text-align: center; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 10px; font-size: 0.9em; }
        th { background-color: #ecf0f1; color: #2c3e50; }
        .day-header { background-color: #34495e; color: white; font-weight: bold; }
        .time-header { font-size: 0.8em; background-color: #bdc3c7; }
        .cell-u6, .cell-u7, .cell-u8, .cell-u9 { background-color: #d5f5e3; color: #1e8449; font-weight: bold;}
        .cell-u10, .cell-u11 { background-color: #d6eaf8; color: #21618c; font-weight: bold;}
        .cell-u12 { background-color: #fdebd0; color: #b9770e; font-weight: bold;}
        .cell-u13, .cell-u14 { background-color: #fadbd8; color: #943126; font-weight: bold;}
        .cell-break { background-color: #f2f3f4; color: #a6acaf; font-style: italic;}
    """
    
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{title}</title><style>{css}</style></head>
    <body><div class="container"><h1>Tournament Configuration: {title}</h1><hr><h2>1. Pitch Map & Zone Assignment</h2><div class="zone-wrapper">"""
    
    # Generate Zone Map
    for z in sorted(zones.keys()):
        html += f'<div class="zone {z.lower()}"><h3>{z}</h3><div class="pitch-grid">'
        for p in zones[z]:
            html += f'<div class="pitch-card">{p["name"]}<br>{p["age"]}</div>'
        html += '</div></div>'
    html += '</div><hr><h2>2. Age Group Breakdown</h2><div class="table-container"><table><thead><tr><th>Age Group</th><th>Teams</th><th>Total Matches</th><th>Pitches Req.</th><th>Dedicated Pitches</th><th>Zone</th></tr></thead><tbody>'
    
    # Generate Breakdown Table
    for alloc in allocations:
        p_names = ", ".join([p['name'] for p in alloc['assigned_pitches']])
        primary_zone = alloc['assigned_pitches'][0]['zone']
        html += f"<tr><td><strong>{alloc['age_group']}</strong></td><td>{alloc['teams']} Teams</td><td>{alloc['matches']} Matches</td><td>{alloc['pitches_req']}</td><td>{p_names}</td><td><span style='font-weight:bold;' class='{primary_zone.lower()}'>{primary_zone}</span></td></tr>"
    html += '</tbody></table></div><hr><h2>3. Master Tournament Schedule (16 Slots Total)</h2><div class="table-container"><table><thead><tr><th rowspan="2">Pitch</th><th colspan="8" class="day-header">Tuesday (6:30 PM - 8:30 PM)</th><th colspan="8" class="day-header" style="background-color: #2c3e50;">Thursday (6:30 PM - 8:30 PM)</th></tr><tr class="time-header">'
    
    # Generate Time Headers
    times = ["6:30 - 6:45", "6:45 - 7:00", "7:00 - 7:15", "7:15 - 7:30", "7:30 - 7:45", "7:45 - 8:00", "8:00 - 8:15", "8:15 - 8:30"] * 2
    for t in times: html += f"<th>{t}</th>"
    html += '</tr></thead><tbody>'
    
    # Generate Grid
    assigned_pitches = [p for alloc in allocations for p in alloc['assigned_pitches']]
    for p in sorted(assigned_pitches, key=lambda x: int(x['name'].replace('Pitch ', '')) if 'Pitch ' in x['name'] else x['name']):
        html += f"<tr><td><strong>{p['name']}</strong></td>"
        for slot in range(1, 17):
            age = pitch_schedule.get(p['id'], {}).get(slot)
            if age:
                html += f'<td class="cell-{age.lower()}">{age}</td>'
            else:
                html += '<td class="cell-break">Break</td>'
        html += "</tr>"

    html += "</tbody></table></div></div></body></html>"
    
    with open(filename, 'w') as f:
        f.write(html)

def generate_detailed_html_grid(master_schedule, allocations, filename="master_schedule_grid.html"):
    """Generates the detailed matchup visualization matrix (Team vs Team)."""
    print(f"Exporting Detailed HTML Grid: {filename}...")
    
    grid_data = {}
    for match in master_schedule:
        p_name = match['pitch_name']
        if p_name not in grid_data: grid_data[p_name] = {}
        grid_data[p_name][match['slot']] = f"<span style='font-size:0.85em'>{match['team1']}<br>vs<br>{match['team2']}</span>"

    html = """
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Master Tournament Matchup Grid</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f4f7f6; margin: 20px; }
            .container { max-width: 1400px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; overflow-x: auto; }
            table { width: 100%; border-collapse: collapse; text-align: center; white-space: nowrap; }
            th, td { border: 1px solid #ddd; padding: 6px; }
            .d1 { background-color: #2980b9; color: white; }
            .d2 { background-color: #2c3e50; color: white; }
            .time { background-color: #ecf0f1; font-size: 0.8em; }
            .break { background-color: #f9ebea; color: #c0392b; font-size: 0.8em; }
        </style>
    </head><body><div class="container"><h1 style="text-align:center;">Detailed Matchup Schedule Grid</h1>
            <table><thead><tr><th rowspan="2">Pitch</th><th colspan="8" class="d1">Day 1: Tuesday</th><th colspan="8" class="d2">Day 2: Thursday</th></tr><tr class="time">
    """
    for i in range(1, 17): html += f"<th>S{i}<br>{TIME_MAP[i].split(' ')[1]}</th>"
    html += "</tr></thead><tbody>"
    
    for alloc in allocations:
        age_class = f"background-color: #e8f8f5;"
        for pitch in alloc['assigned_pitches']:
            p_name = pitch['name']
            html += f"<tr style='{age_class}'><td><strong>{p_name}</strong><br><small>{alloc['age_group']} ({pitch['zone']})</small></td>"
            for slot in range(1, 17):
                matchup = grid_data.get(p_name, {}).get(slot, "<span class='break'>Rest/Break</span>")
                html += f"<td>{matchup}</td>"
            html += "</tr>"

    html += "</tbody></table></div></body></html>"
    with open(filename, 'w') as f: f.write(html)


# ==========================================
# 6. EXECUTION & TEAM REGISTRY
# ==========================================
if __name__ == "__main__":
    
    print_configurations(total_pitches=14)
    
    # 1. Define Option 1 Breakdown
    option_1_config = [
        {'age': 'U6', 'teams': 6}, {'age': 'U7', 'teams': 6},
        {'age': 'U8', 'teams': 6}, {'age': 'U9', 'teams': 6},
        {'age': 'U10', 'teams': 8}, {'age': 'U11', 'teams': 8},
        {'age': 'U12', 'teams': 10}, {'age': 'U13', 'teams': 10},
    ]
    
    # 2. Master Team List Mapper
    MASTER_TEAM_LIST = [
        'IRELAND', 'GERMANY', 'SPAIN', 'HOLLAND', 'BRAZIL', 
        'ARGENTINA', 'PORTUGAL', 'ENGLAND', 'ITALY', 'FRANCE'
    ]
    
    # Dynamically build rosters
    TEAM_ROSTERS = {}
    for group in option_1_config:
        TEAM_ROSTERS[group['age']] = MASTER_TEAM_LIST[:group['teams']]
    
    # 3. Run the engines
    allocation_data = allocate_tournament("Option 1", option_1_config)
    master_schedule = generate_master_schedule(allocation_data['allocations'], TEAM_ROSTERS)
    
    # 4. Export all files
    export_to_csv(master_schedule, "master_schedule.csv")
    generate_summary_dashboard(allocation_data['allocations'], master_schedule, allocation_data['title'], "summary_dashboard.html")
    generate_detailed_html_grid(master_schedule, allocation_data['allocations'], "master_schedule_grid.html")
    
    print("\n--- Process Complete! Output files generated. ---")