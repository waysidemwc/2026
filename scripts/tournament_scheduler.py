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
    # Discovery defaults for player estimates
    blocks = [
        {'teams': 6, 'pitches': 1, 'matches': 15, 'players_per_team': 5},
        {'teams': 8, 'pitches': 2, 'matches': 28, 'players_per_team': 8},
        {'teams': 10, 'pitches': 3, 'matches': 45, 'players_per_team': 9}
    ]
    valid_configs = []
    
    for num_age_groups in range(4, 16):
        for combo in itertools.combinations_with_replacement(blocks, num_age_groups):
            used_pitches = sum(item['pitches'] for item in combo)
            if used_pitches == total_pitches:
                total_teams = sum(item['teams'] for item in combo)
                total_matches = sum(item['matches'] for item in combo)
                total_players = sum(item['teams'] * item['players_per_team'] for item in combo)
                
                counts = {6: 0, 8: 0, 10: 0}
                for item in combo:
                    counts[item['teams']] += 1
                    
                config_summary = {
                    'num_age_groups': num_age_groups,
                    'total_teams': total_teams,
                    'total_matches': total_matches,
                    'total_players': total_players,
                    'used_pitches': used_pitches,
                    'spare_pitches': 0,
                    'breakdown': counts
                }
                
                if config_summary not in valid_configs:
                    valid_configs.append(config_summary)
                    
    # Sort by total teams (desc), then total matches (desc)
    valid_configs.sort(key=lambda x: (x['total_teams'], x['total_matches']), reverse=True)
    return valid_configs

def print_configurations(total_pitches):
    configs = discover_configurations(total_pitches)
    print(f"\n=======================================================")
    print(f" DISCOVERED CONFIGURATIONS FOR {total_pitches} PITCHES")
    print(f"=======================================================\n")
    
    for i, config in enumerate(configs, 1):
        spare_text = f"({config['spare_pitches']} spare)" if config['spare_pitches'] > 0 else "(No spare pitches)"
        print(f"Option {i}: {config['num_age_groups']} Age Groups")
        print(f"  TOTAL:")
        print(f"  - {config['total_teams']} Teams")
        print(f"  - {config['total_players']} Players (approx)")
        print(f"  - {config['total_matches']} Matches")
        print(f"  - {config['used_pitches']} Pitches {spare_text}")
        print(f"  BREAKDOWN:")
        if config['breakdown'][6] > 0: print(f"    - {config['breakdown'][6]} brackets of 6 Teams (1 pitch each)")
        if config['breakdown'][8] > 0: print(f"    - {config['breakdown'][8]} brackets of 8 Teams (2 pitches each)")
        if config['breakdown'][10] > 0: print(f"    - {config['breakdown'][10]} brackets of 10 Teams (3 pitches each)")
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
    
    # 1. Initialize Zone-based Inventory
    zone_inventory = {
        'JP1': [p for p in PITCH_INVENTORY if p['zone'] == 'JP1'],
        'JP2': [p for p in PITCH_INVENTORY if p['zone'] == 'JP2'],
        'JP3': [p for p in PITCH_INVENTORY if p['zone'] == 'JP3'],
        'JP4': [p for p in PITCH_INVENTORY if p['zone'] == 'JP4'],
    }
    
    # 2. Sort age groups by size (largest first) to handle 3-pitch groups early
    sorted_groups = sorted(age_groups, key=lambda x: get_requirements(x['teams'])[1], reverse=True)
    
    allocations_map = {}
    
    for group in sorted_groups:
        age = group['age']
        teams = group['teams']
        players_per = group.get('players_per_team', 0)
        matches, pitches_needed = get_requirements(teams)
        
        placed = False
        # Try to find a zone with enough capacity to keep the group unified
        for z_name in ['JP1', 'JP2', 'JP3', 'JP4']:
            if len(zone_inventory[z_name]) >= pitches_needed:
                assigned = [zone_inventory[z_name].pop(0) for _ in range(pitches_needed)]
                allocations_map[age] = {
                    'age_group': age,
                    'teams': teams,
                    'players_per_team': players_per,
                    'total_players': teams * players_per,
                    'matches': matches,
                    'pitches_req': pitches_needed,
                    'assigned_pitches': assigned
                }
                placed = True
                break
        
        if not placed:
            # Fallback
            assigned = []
            for z_name in ['JP1', 'JP2', 'JP3', 'JP4']:
                while zone_inventory[z_name] and len(assigned) < pitches_needed:
                    assigned.append(zone_inventory[z_name].pop(0))
            
            if len(assigned) == pitches_needed:
                allocations_map[age] = {
                    'age_group': age,
                    'teams': teams,
                    'players_per_team': players_per,
                    'total_players': teams * players_per,
                    'matches': matches,
                    'pitches_req': pitches_needed,
                    'assigned_pitches': assigned
                }
            else:
                raise ValueError(f"Critically failed to allocate {pitches_needed} pitches for {age}")

    final_allocations = []
    for g in age_groups:
        final_allocations.append(allocations_map[g['age']])
        
    return {'title': option_name, 'allocations': final_allocations}


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
        
        roster = team_rosters.get(age, [f"{age}-Team {i}" for i in range(1, team_count + 1)])
        
        group_matches = []
        if team_count == 6: group_matches = schedule_6_teams(roster)
        elif team_count == 8: group_matches = schedule_8_teams(roster)
        elif team_count == 10: group_matches = schedule_10_teams(roster)
            
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
    sorted_schedule = sorted(master_schedule, key=lambda x: (x['slot'], x['zone'], x['pitch_id']))
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(sorted_schedule)

def generate_summary_dashboard(allocations, master_schedule, title, filename="summary_dashboard.html", config_info=None, index_link=None, discovery_configs=None):
    """Generates the high-level dashboard with Zone Map, Breakdown, and Abstract Schedule Grid."""
    print(f"Exporting Summary Dashboard: {filename}...")
    
    total_teams = sum(a['teams'] for a in allocations)
    total_matches = len(master_schedule)
    total_players = config_info['total_players'] if config_info else sum(a.get('total_players', 0) for a in allocations)
    used_pitches = sum(a['pitches_req'] for a in allocations)
    spare_pitches = config_info['spare_pitches'] if config_info else 0
    spare_text = f"({spare_pitches} spare)" if spare_pitches > 0 else "(No spare pitches)"

    zones = {}
    for alloc in allocations:
        for pitch in alloc['assigned_pitches']:
            z = pitch['zone']
            if z not in zones: zones[z] = []
            zones[z].append({'name': pitch['name'], 'age': alloc['age_group']})
            
    pitch_schedule = {}
    for match in master_schedule:
        p_id = match['pitch_id']
        if p_id not in pitch_schedule: pitch_schedule[p_id] = {}
        pitch_schedule[p_id][match['slot']] = match['age_group']

    nav_html = f'<div style="text-align: center; margin-bottom: 20px;"><a href="{index_link}" style="color: #3498db; text-decoration: none; font-weight: bold;">&larr; Back to Recommended Proposal Index</a></div>' if index_link else ""
    
    css = """
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f7f6; color: #333; }
        h1, h2 { text-align: center; color: #2c3e50; margin-bottom: 10px; }
        .container { max-width: 1200px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .summary-bar { display: flex; justify-content: space-around; background: #2c3e50; color: white; padding: 15px; border-radius: 8px; margin-bottom: 30px; }
        .summary-item { text-align: center; }
        .summary-item .val { display: block; font-size: 1.5em; font-weight: bold; }
        .summary-item .lbl { font-size: 0.8em; text-transform: uppercase; opacity: 0.8; }
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
        .cell-u6, .cell-u7, .cell-u8, .cell-u9, .cell-u10, .cell-u11, .cell-u12, .cell-u13, .cell-u14, .cell-u15, .cell-u16, .cell-u17, .cell-u18, .cell-u19 { font-weight: bold; }
        .cell-u6, .cell-u7, .cell-u8, .cell-u9 { background-color: #d5f5e3; color: #1e8449; }
        .cell-u10, .cell-u11 { background-color: #d6eaf8; color: #21618c; }
        .cell-u12, .cell-u13 { background-color: #fdebd0; color: #b9770e; }
        .cell-u14, .cell-u15, .cell-u16, .cell-u17, .cell-u18, .cell-u19 { background-color: #fadbd8; color: #943126; }
        .cell-break { background-color: #f2f3f4; color: #a6acaf; font-style: italic;}
        .age-label { font-size: 0.8em; }
        .discovery-list { margin-top: 50px; border-top: 4px solid #eee; padding-top: 30px; }
        .discovery-table { font-size: 0.85em; }
        .discovery-table a { color: #3498db; text-decoration: none; font-weight: bold; }
        .discovery-table tr:hover { background-color: #f9f9f9; }
    """
    
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{title}</title><style>{css}</style></head>
    <body><div class="container">{nav_html}<h1>Tournament Configuration: {title}</h1>
    <div class="summary-bar">
        <div class="summary-item"><span class="val">{len(allocations)}</span><span class="lbl">Age Groups</span></div>
        <div class="summary-item"><span class="val">{total_teams}</span><span class="lbl">Total Teams</span></div>
        <div class="summary-item"><span class="val">{total_players}</span><span class="lbl">Total Players</span></div>
        <div class="summary-item"><span class="val">{total_matches}</span><span class="lbl">Total Matches</span></div>
        <div class="summary-item"><span class="val">{used_pitches}</span><span class="lbl">Pitches {spare_text}</span></div>
    </div>
    <hr><h2>1. Pitch Map & Zone Assignment</h2><div class="zone-wrapper">"""
    
    for z in sorted(zones.keys()):
        html += f'<div class="zone {z.lower()}"><h3>{z}</h3><div class="pitch-grid">'
        for p in zones[z]:
            html += f'<div class="pitch-card">{p["name"]}<br><span class="age-label">{p["age"]}</span></div>'
        html += '</div></div>'
    html += '</div><hr><h2>2. Age Group Breakdown</h2><div class="table-container"><table><thead><tr><th>Age Group</th><th>Teams</th><th>Players/Team</th><th>Total Players</th><th>Matches</th><th>Pitches Req.</th><th>Dedicated Pitches</th><th>Zone</th></tr></thead><tbody>'
    
    for alloc in allocations:
        p_names = ", ".join([p['name'] for p in alloc['assigned_pitches']])
        primary_zone = alloc['assigned_pitches'][0]['zone']
        html += f"<tr><td><strong>{alloc['age_group']}</strong></td><td>{alloc['teams']} Teams</td><td>{alloc.get('players_per_team', 'N/A')}</td><td>{alloc.get('total_players', 'N/A')}</td><td>{alloc['matches']} Matches</td><td>{alloc['pitches_req']}</td><td>{p_names}</td><td><span style='font-weight:bold;' class='{primary_zone.lower()}'>{primary_zone}</span></td></tr>"
    html += '</tbody></table></div><hr><h2>3. Master Tournament Schedule (16 Slots Total)</h2><div class="table-container"><table><thead><tr><th rowspan="2">Pitch</th><th colspan="8" class="day-header">Tuesday (6:30 PM - 8:30 PM)</th><th colspan="8" class="day-header" style="background-color: #2c3e50;">Thursday (6:30 PM - 8:30 PM)</th></tr><tr class="time-header">'
    
    times = ["6:30 - 6:45", "6:45 - 7:00", "7:00 - 7:15", "7:15 - 7:30", "7:30 - 7:45", "7:45 - 8:00", "8:00 - 8:15", "8:15 - 8:30"] * 2
    for t in times: html += f"<th>{t}</th>"
    html += '</tr></thead><tbody>'
    
    assigned_pitches = [p for alloc in allocations for p in alloc['assigned_pitches']]
    for p in sorted(assigned_pitches, key=lambda x: int(x['name'].replace('Pitch ', '')) if 'Pitch ' in x['name'] else x['name']):
        html += f"<tr><td><strong>{p['name']}</strong></td>"
        for slot in range(1, 17):
            age = pitch_schedule.get(p['id'], {}).get(slot)
            if age:
                age_clean = age.split(' ')[0].lower()
                html += f'<td class="cell-{age_clean}">{age}</td>'
            else:
                html += '<td class="cell-break">Break</td>'
        html += "</tr>"

    html += "</tbody></table></div>"
    
    if discovery_configs:
        params_html = """
        <div class="discovery-list">
            <hr>
            <h2>Tournament Logic & Parameters</h2>
            <div style="background: #fdfefe; border: 1px solid #dcdfe0; padding: 20px; border-radius: 8px; margin-bottom: 30px; font-size: 0.95em; line-height: 1.6;">
                <div style="display: flex; flex-wrap: wrap; gap: 40px;">
                    <div style="flex: 1; min-width: 300px;">
                        <h4 style="margin-top:0; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">Foundational Constraints</h4>
                        <ul style="padding-left: 20px;">
                            <li><strong>14 pitches</strong> (or 13 Pitches + 1 spare)</li>
                            <li><strong>15 minutes per slot:</strong> 12 min match + 3 min gap</li>
                            <li><strong>Round Robin:</strong> 4 hours total (Tue/Thu 6:30pm - 8:30pm)</li>
                            <li><strong>Minimal Movement:</strong> Age groups are ring-fenced to specific dedicated pitches</li>
                        </ul>
                    </div>
                    <div style="flex: 1; min-width: 300px;">
                        <h4 style="margin-top:0; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">Capacity Math</h4>
                        <ul style="padding-left: 20px;">
                            <li><strong>Total Time:</strong> 240 minutes (16 time slots available)</li>
                            <li><strong>Pitch Capacity:</strong> Max 16 matches per pitch</li>
                            <li><strong>Tournament Cap (13 Pitches):</strong> 208 match slots</li>
                            <li><strong>Tournament Cap (14 Pitches):</strong> 224 match slots</li>
                        </ul>
                    </div>
                </div>
                <h4 style="margin-top:20px; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">The Optimal Team Blocks</h4>
                <p>To maximize pitch efficiency while keeping age groups unified, we use these optimized bracket sizes:</p>
                <div style="display: flex; gap: 15px; flex-wrap: wrap; text-align: center;">
                    <div style="flex: 1; background: #e8f8f5; padding: 10px; border-radius: 5px; border-left: 5px solid #1abc9c;">
                        <strong>6 Teams</strong><br>15 matches | 1 Pitch<br>5 Players per Team
                    </div>
                    <div style="flex: 1; background: #ebf5fb; padding: 10px; border-radius: 5px; border-left: 5px solid #3498db;">
                        <strong>8 Teams</strong><br>28 matches | 2 Pitches<br>8 Players per Team
                    </div>
                    <div style="flex: 1; background: #fef9e7; padding: 10px; border-radius: 5px; border-left: 5px solid #f1c40f;">
                        <strong>10 Teams</strong><br>45 matches | 3 Pitches<br>9 Players per Team
                    </div>
                </div>
            </div>
            <hr>
            <h2>Explore Other Discovery Options</h2>
            <div class="table-container">
                <table class="discovery-table">
                    <thead>
                        <tr>
                            <th>Option</th>
                            <th>Age Groups</th>
                            <th>Total Teams</th>
                            <th>Total Players</th>
                            <th>Total Matches</th>
                            <th>Pitches</th>
                            <th>Dashboard</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        html += params_html
        for i, config in enumerate(discovery_configs, 1):
            suffix = f"option_{i}"
            db_link = f"options_output/summary_dashboard_{suffix}.html"
            html += f"<tr><td><strong>Option {i}</strong></td><td>{config['num_age_groups']}</td><td>{config['total_teams']}</td><td>{config['total_players']}</td><td>{config['total_matches']}</td><td>14</td><td><a href='{db_link}'>View Dashboard</a></td></tr>"
        html += '</tbody></table></div></div>'

    html += "</div></body></html>"
    with open(filename, 'w') as f: f.write(html)

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
def map_config_to_ages(config, start_age=6):
    """Maps a configuration breakdown to a list of age groups with team counts."""
    age_groups = []
    current_age = start_age
    for teams in [6, 8, 10]:
        count = config['breakdown'][teams]
        players_map = {6: 5, 8: 8, 10: 9}
        for _ in range(count):
            age_groups.append({'age': f'U{current_age}', 'teams': teams, 'players_per_team': players_map[teams]})
            current_age += 1
    return age_groups

def generate_readme_index(configs, output_dir, filename="README.md", final_info=None):
    """Generates a README.md index linking to all generated options."""
    print(f"Generating README Index: {filename}...")
    content = "# Wayside Mini World Cup 2026 - Tournament Configurations\n\n"
    if final_info:
        content += "## 🏆 RECOMMENDED PROPOSAL\n\n"
        content += "This configuration is tailored to the specific age group and team count requirements provided.\n\n"
        content += f"- **Dashboard:** [View Interactive Dashboard](index.html)\n"
        content += f"- **Matchup Grid:** [View Detailed Matchup Grid](master_schedule_grid_final.html)\n"
        content += f"- **Data:** [Download CSV Schedule](master_schedule_final.csv)\n\n"
        content += "### Proposal Summary:\n"
        content += f"- **{final_info['num_age_groups']}** Age Groups\n"
        content += f"- **{final_info['total_teams']}** Total Teams\n"
        content += f"- **{final_info['total_players']}** Total Players\n"
        content += f"- **{final_info['total_matches']}** Total Matches\n"
        content += f"- **{final_info['used_pitches']}** Pitches (No spare pitches)\n\n"
        content += "---\n\n"
    content += "## Discovery Options\n\n"
    content += "| Option | Age Groups | Teams | Players | Matches | Dashboards |\n"
    content += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    for i, config in enumerate(configs, 1):
        suffix = f"option_{i}"
        dashboard = f"[Dashboard](options_output/summary_dashboard_{suffix}.html)"
        content += f"| **Option {i}** | {config['num_age_groups']} | {config['total_teams']} | {config['total_players']} | {config['total_matches']} | {dashboard} |\n"
    content += "\n## Detailed Option Summaries\n\n"
    for i, config in enumerate(configs, 1):
        content += f"### Option {i}\n"
        content += f"- **{config['num_age_groups']}** Age Groups\n"
        content += f"- **{config['total_teams']}** Total Teams\n"
        content += f"- **{config['total_players']}** Total Players\n"
        content += f"- **{config['total_matches']}** Total Matches\n"
        content += f"- **{config['used_pitches']}** Pitches (No spare pitches)\n\n"
        content += "#### Breakdown:\n"
        if config['breakdown'][6] > 0: content += f"- {config['breakdown'][6]} brackets of 6 Teams (1 pitch each | 5 Players per Team)\n"
        if config['breakdown'][8] > 0: content += f"- {config['breakdown'][8]} brackets of 8 Teams (2 pitches each | 8 Players per Team)\n"
        if config['breakdown'][10] > 0: content += f"- {config['breakdown'][10]} brackets of 10 Teams (3 pitches each | 9 Players per Team)\n"
        content += "\n---\n\n"
    with open(filename, 'w') as f: f.write(content)

if __name__ == "__main__":
    PITCH_COUNT = 14
    configs = discover_configurations(total_pitches=PITCH_COUNT)
    if not configs: exit(1)

    output_dir = "options_output"
    if not os.path.exists(output_dir): os.makedirs(output_dir)
        
    for i, selected_config in enumerate(configs, 1):
        option_label = f"Option {i}"
        file_suffix = f"option_{i}"
        age_groups_config = map_config_to_ages(selected_config)
        MASTER_TEAM_LIST = ['IRELAND', 'GERMANY', 'SPAIN', 'HOLLAND', 'BRAZIL', 'ARGENTINA', 'PORTUGAL', 'ENGLAND']
        TEAM_ROSTERS = {group['age']: MASTER_TEAM_LIST[:group['teams']] for group in age_groups_config}
        allocation_data = allocate_tournament(option_label, age_groups_config)
        master_schedule = generate_master_schedule(allocation_data['allocations'], TEAM_ROSTERS)
        export_to_csv(master_schedule, os.path.join(output_dir, f"master_schedule_{file_suffix}.csv"))
        generate_summary_dashboard(allocation_data['allocations'], master_schedule, allocation_data['title'], os.path.join(output_dir, f"summary_dashboard_{file_suffix}.html"), config_info=selected_config, index_link="../index.html")
        generate_detailed_html_grid(master_schedule, allocation_data['allocations'], os.path.join(output_dir, f"master_schedule_grid_{file_suffix}.html"))

    print("\nGenerating FINAL RECOMMENDED PROPOSAL...")
    # Optimal Mix: U6/U7 Boys (6), U7/U8 Girls (6), 6 others with 8 teams each
    final_proposal_config = [
        {'age': 'U6/U7 Boys', 'teams': 6, 'players_per_team': 5},
        {'age': 'U8 Boys', 'teams': 8, 'players_per_team': 8},
        {'age': 'U9 Mixed', 'teams': 8, 'players_per_team': 8},
        {'age': 'U10 Mixed', 'teams': 8, 'players_per_team': 8},
        {'age': 'U11 Mixed', 'teams': 8, 'players_per_team': 8},
        {'age': 'U12 Mixed', 'teams': 8, 'players_per_team': 8},
        {'age': 'U13 Mixed', 'teams': 8, 'players_per_team': 8},
        {'age': 'U7/U8 Girls', 'teams': 6, 'players_per_team': 5},
    ]
    
    final_info = {
        'num_age_groups': len(final_proposal_config),
        'total_teams': sum(g['teams'] for g in final_proposal_config),
        'total_players': sum(g['teams'] * g['players_per_team'] for g in final_proposal_config),
        'total_matches': sum(get_requirements(g['teams'])[0] for g in final_proposal_config),
        'used_pitches': 14,
        'spare_pitches': 0
    }

    MASTER_TEAM_LIST = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10']
    TEAM_ROSTERS_FINAL = {group['age']: MASTER_TEAM_LIST[:group['teams']] for group in final_proposal_config}
    allocation_final = allocate_tournament("Final Recommended Proposal", final_proposal_config)
    schedule_final = generate_master_schedule(allocation_final['allocations'], TEAM_ROSTERS_FINAL)
    export_to_csv(schedule_final, "master_schedule_final.csv")
    generate_summary_dashboard(allocation_final['allocations'], schedule_final, "Final Recommended Proposal", "index.html", config_info=final_info, index_link=None, discovery_configs=configs)
    generate_detailed_html_grid(schedule_final, allocation_final['allocations'], "master_schedule_grid_final.html")
    generate_readme_index(configs, output_dir, final_info=final_info)
    print(f"\n--- Process Complete! Final Proposal and {len(configs)} options generated. ---")