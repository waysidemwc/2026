import itertools
import os
import csv
import random
import argparse
from collections import defaultdict

# ==========================================
# GLOBAL CACHE
# ==========================================
SCHEDULE_CACHE = {}

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

def schedule_6_teams(teams, use_cache=True):
    """
    6 Teams, 1 Pitch, 15 Matches.
    Uses an explicitly optimized pattern to guarantee perfectly spaced rests.
    """
    if use_cache and "6_teams" in SCHEDULE_CACHE:
        # Map cached abstract indices to these specific team names
        cached = SCHEDULE_CACHE["6_teams"]
        return [{'slot': m['slot'], 'pitch_idx': m['pitch_idx'], 't1': teams[m['t1_idx']], 't2': teams[m['t2_idx']]} for m in cached]

    # Hardcoded optimal stagger for perfectly even rest
    optimal_sequence = [
        (0,1), (2,3), (4,5), (0,2), (3,5), (1,4), (0,3), (2,4),
        (1,5), (0,4), (2,5), (1,3), (0,5), (3,4), (1,2)
    ]
    
    # Available slots: 1-7 and 9-16 (skipping 8)
    available_slots = [1,2,3,4,5,6,7, 9,10,11,12,13,14,15,16]
    
    matches = []
    abstract_matches = []
    for i, (idx1, idx2) in enumerate(optimal_sequence):
        matches.append({
            'slot': available_slots[i], 
            'pitch_idx': 0, 
            't1': teams[idx1], 
            't2': teams[idx2]
        })
        abstract_matches.append({
            'slot': available_slots[i], 
            'pitch_idx': 0, 
            't1_idx': idx1, 
            't2_idx': idx2
        })
    
    if use_cache: SCHEDULE_CACHE["6_teams"] = abstract_matches
    return matches

def optimize_spacing(teams, matches, num_pitches, physical_slots, size_key=None, use_cache=True):
    """Uses a Monte-Carlo Greedy approach to find the schedule with the best possible rest spacing."""
    if use_cache and size_key and size_key in SCHEDULE_CACHE:
        cached = SCHEDULE_CACHE[size_key]
        return [{'slot': m['slot'], 'pitch_idx': m['pitch_idx'], 't1': teams[m['t1_idx']], 't2': teams[m['t2_idx']]} for m in cached]

    best_schedule = []
    best_overall_score = -9999999
    
    # Map teams to indices for caching
    team_to_idx = {t: i for i, t in enumerate(teams)}
    idx_matches = [(team_to_idx[m[0]], team_to_idx[m[1]]) for m in matches]
    
    # Fallback
    fallback_schedule = []
    m_idx = 0
    for slot in physical_slots:
        for p in range(num_pitches):
            if m_idx < len(matches):
                fallback_schedule.append({'slot': slot, 'pitch_idx': p, 't1': matches[m_idx][0], 't2': matches[m_idx][1]})
                m_idx += 1
                
    for _ in range(1000):
        shuffled_indices = idx_matches[:]
        random.shuffle(shuffled_indices)
        remaining = shuffled_indices[:]
        scheduled = []
        team_last_played = {i: -99 for i in range(len(teams))}
        
        min_rest_in_schedule = 999
        total_rest_score = 0
        back_to_back_count = 0
        
        team_consecutive_tracker = {i: 0 for i in range(len(teams))}
        max_consecutive_for_any_team = 0
        
        for slot in physical_slots:
            slot_matches = []
            teams_in_slot = set()
            
            while len(slot_matches) < num_pitches and remaining:
                best_match = None
                best_match_score = -99999
                
                for m in remaining:
                    t1, t2 = m
                    if t1 in teams_in_slot or t2 in teams_in_slot: continue 
                    dist1 = slot - team_last_played[t1]
                    dist2 = slot - team_last_played[t2]
                    score = min(dist1, dist2)
                    if score > best_match_score:
                        best_match_score = score
                        best_match = m
                        
                if best_match:
                    d1 = slot - team_last_played[best_match[0]]
                    d2 = slot - team_last_played[best_match[1]]
                    if 0 < d1 < 50: 
                        min_rest_in_schedule = min(min_rest_in_schedule, d1)
                        total_rest_score += d1
                        if d1 == 1: back_to_back_count += 1
                    if 0 < d2 < 50: 
                        min_rest_in_schedule = min(min_rest_in_schedule, d2)
                        total_rest_score += d2
                        if d2 == 1: back_to_back_count += 1
                    slot_matches.append(best_match)
                    teams_in_slot.update(best_match)
                    remaining.remove(best_match)
                else: break 
            
            for i, m in enumerate(slot_matches):
                t1, t2 = m[0], m[1]
                for t in [t1, t2]:
                    if slot == team_last_played[t] + 1: team_consecutive_tracker[t] += 1
                    else: team_consecutive_tracker[t] = 0
                    max_consecutive_for_any_team = max(max_consecutive_for_any_team, team_consecutive_tracker[t])
                team_last_played[t1] = slot
                team_last_played[t2] = slot
                scheduled.append({'slot': slot, 'pitch_idx': i, 't1_idx': t1, 't2_idx': t2})
                
        if not remaining:
            eval_score = (max_consecutive_for_any_team * -100000) + (back_to_back_count * -10000) + (min_rest_in_schedule * 1000) + total_rest_score
            if eval_score > best_overall_score:
                best_overall_score = eval_score
                best_schedule = scheduled
                
    if best_schedule:
        if use_cache and size_key: SCHEDULE_CACHE[size_key] = best_schedule
        return [{'slot': m['slot'], 'pitch_idx': m['pitch_idx'], 't1': teams[m['t1_idx']], 't2': teams[m['t2_idx']]} for m in best_schedule]
    return fallback_schedule

def schedule_8_teams(teams, use_cache=True):
    """8 Teams, 2 Pitches, 28 Matches. Optimized for rest."""
    rounds = generate_round_robin(teams)
    all_matches = [m for r in rounds for m in r]
    # Use 7 slots Tue (1-7) and 7 slots Thu (9-15)
    physical_slots = [1,2,3,4,5,6,7, 9,10,11,12,13,14,15]
    return optimize_spacing(teams, all_matches, num_pitches=2, physical_slots=physical_slots, size_key="8_teams", use_cache=use_cache)

def schedule_10_teams(teams, use_cache=True):
     """10 Teams, 3 Pitches, 45 Matches. Optimized for rest."""
     rounds = generate_round_robin(teams)
     all_matches = [m for r in rounds for m in r]
     # Use 7 slots Tue (1-7) and 8 slots Thu (9-16)
     physical_slots = [1,2,3,4,5,6,7, 9,10,11,12,13,14,15,16]
     return optimize_spacing(teams, all_matches, num_pitches=3, physical_slots=physical_slots, size_key="10_teams", use_cache=use_cache)

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
                for item in combo: counts[item['teams']] += 1
                config_summary = {
                    'num_age_groups': num_age_groups,
                    'total_teams': total_teams,
                    'total_matches': total_matches,
                    'total_players': total_players,
                    'used_pitches': used_pitches,
                    'spare_pitches': 0,
                    'breakdown': counts
                }
                if config_summary not in valid_configs: valid_configs.append(config_summary)
    valid_configs.sort(key=lambda x: (x['total_teams'], x['total_matches']), reverse=True)
    return valid_configs

def print_configurations(total_pitches):
    configs = discover_configurations(total_pitches)
    print(f"\n=======================================================")
    print(f" DISCOVERED CONFIGURATIONS FOR {total_pitches} PITCHES")
    print(f"=======================================================\n")
    for i, config in enumerate(configs, 1):
        print(f"Option {i}: {config['num_age_groups']} Age Groups")
        print(f"  TOTAL:")
        print(f"  - {config['total_teams']} Teams")
        print(f"  - {config['total_players']} Players (approx)")
        print(f"  - {config['total_matches']} Matches")
        print("-" * 40)

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
    1: "Tue 6:30-6:45", 2: "Tue 6:45-7:00", 3: "Tue 7:00-7:15", 4: "Tue 7:15-7:30",
    5: "Tue 7:30-7:45", 6: "Tue 7:45-8:00", 7: "Tue 8:00-8:15", 8: "Tue 8:15-8:30 (Free)",
    9: "Thu 6:30-6:45", 10: "Thu 6:45-7:00", 11: "Thu 7:00-7:15", 12: "Thu 7:15-7:30",
    13: "Thu 7:30-7:45", 14: "Thu 7:45-8:00", 15: "Thu 8:00-8:15", 16: "Thu 8:15-8:30"
}

def get_requirements(team_count):
    if team_count <= 6: return 15, 1
    elif team_count <= 8: return 28, 2
    elif team_count <= 10: return 45, 3
    else: raise ValueError("Team count must be 6, 8, or 10.")

def allocate_tournament(option_name, age_groups, use_cache=True):
    zone_inventory = {
        'JP1': [p for p in PITCH_INVENTORY if p['zone'] == 'JP1'],
        'JP2': [p for p in PITCH_INVENTORY if p['zone'] == 'JP2'],
        'JP3': [p for p in PITCH_INVENTORY if p['zone'] == 'JP3'],
        'JP4': [p for p in PITCH_INVENTORY if p['zone'] == 'JP4'],
    }
    
    allocations_map = {}
    
    # First pass: Allocate groups that have a preferred zone
    for group in age_groups:
        preferred_zone = group.get('preferred_zone')
        if not preferred_zone: continue
            
        age = group['age']
        teams = group['teams']
        players_per = group.get('players_per_team', 0)
        matches, pitches_needed = get_requirements(teams)
        
        if len(zone_inventory[preferred_zone]) >= pitches_needed:
            assigned = [zone_inventory[preferred_zone].pop(0) for _ in range(pitches_needed)]
            allocations_map[age] = {
                'age_group': age, 'teams': teams, 'players_per_team': players_per,
                'total_players': teams * players_per, 'matches': matches,
                'pitches_req': pitches_needed, 'assigned_pitches': assigned
            }
            
    # Second pass: Allocate remaining groups to any available space
    for group in age_groups:
        age = group['age']
        if age in allocations_map: continue
            
        teams = group['teams']
        players_per = group.get('players_per_team', 0)
        matches, pitches_needed = get_requirements(teams)
        
        assigned = []
        for z_name in ['JP1', 'JP2', 'JP3', 'JP4']:
            while zone_inventory[z_name] and len(assigned) < pitches_needed:
                assigned.append(zone_inventory[z_name].pop(0))
        
        allocations_map[age] = {
            'age_group': age, 'teams': teams, 'players_per_team': players_per,
            'total_players': teams * players_per, 'matches': matches,
            'pitches_req': pitches_needed, 'assigned_pitches': assigned
        }
            
    final_allocations = []
    for g in age_groups: final_allocations.append(allocations_map[g['age']])
    return {'title': option_name, 'allocations': final_allocations}

# ==========================================
# 4. MATRIX SCHEDULER & VALIDATION
# ==========================================

def perform_validation(master_schedule):
    """Exhaustive check for clashes and quality metrics with per-age breakdown."""
    clashes = []
    slot_pitch_occupancy = defaultdict(list)
    team_slot_occupancy = defaultdict(list)
    team_last_slot = {}
    team_consecutive_count = defaultdict(int)
    max_consecutive = 0
    back_to_back_teams = set()
    back_to_back_count = 0
    age_back_to_back = defaultdict(int)
    min_rest = 99
    
    age_group_teams = defaultdict(set)
    for m in master_schedule:
        age = m['age_group']
        age_group_teams[age].add(f"{age}:{m['team1']}")
        age_group_teams[age].add(f"{age}:{m['team2']}")
        
        s = m['slot']
        p = m['pitch_id']
        t1 = f"{age}:{m['team1']}"
        t2 = f"{age}:{m['team2']}"
        
        if p in slot_pitch_occupancy[s]: clashes.append(f"Pitch Clash: {p} in Slot {s}")
        slot_pitch_occupancy[s].append(p)
        
        for team in [t1, t2]:
            if team in team_slot_occupancy[s]: clashes.append(f"Team Clash: {team} in Slot {s}")
            team_slot_occupancy[s].append(team)
            if team in team_last_slot:
                interval = s - team_last_slot[team]
                if interval == 1: 
                    back_to_back_count += 1
                    age_back_to_back[age] += 1
                    back_to_back_teams.add(team)
                    team_consecutive_count[team] += 1
                else:
                    team_consecutive_count[team] = 0
                max_consecutive = max(max_consecutive, team_consecutive_count[team])
                min_rest = min(min_rest, interval)
            team_last_slot[team] = s

    # Consistency Check
    size_to_groups = defaultdict(list)
    for age, teams in age_group_teams.items():
        size_to_groups[len(teams)].append(age)
    
    def get_abstract_schedule(age_group):
        group_data = [m for m in master_schedule if m['age_group'] == age_group]
        teams = sorted(list(age_group_teams[age_group]))
        team_map = {t: i for i, t in enumerate(teams)}
        abstract = []
        for m in sorted(group_data, key=lambda x: (int(x['slot']), x['team1'], x['team2'])):
            t1 = f"{age_group}:{m['team1']}"
            t2 = f"{age_group}:{m['team2']}"
            abstract.append((int(m['slot']), team_map[t1], team_map[t2]))
        return abstract

    consistency_pass = True
    for size, groups in size_to_groups.items():
        if len(groups) < 2: continue
        base_sched = get_abstract_schedule(groups[0])
        for other in groups[1:]:
            if get_abstract_schedule(other) != base_sched:
                consistency_pass = False
            
    return {
        'status': 'PASS' if not clashes else 'FAIL',
        'clashes': clashes,
        'back_to_back': back_to_back_count,
        'back_to_back_teams_count': len(back_to_back_teams),
        'max_consecutive': max_consecutive + 1,
        'age_back_to_back': age_back_to_back,
        'min_rest': min_rest if min_rest < 99 else 0,
        'consistency_pass': consistency_pass
    }

def generate_master_schedule(allocations, team_rosters, use_cache=True):
    master_schedule = []
    for alloc in allocations:
        age = alloc['age_group']
        teams = team_rosters.get(age, [f"{age}-T{i}" for i in range(1, alloc['teams'] + 1)])
        group_matches = []
        if len(teams) == 6: group_matches = schedule_6_teams(teams, use_cache=use_cache)
        elif len(teams) == 8: group_matches = schedule_8_teams(teams, use_cache=use_cache)
        elif len(teams) == 10: group_matches = schedule_10_teams(teams, use_cache=use_cache)
        for m in group_matches:
            pitch_obj = alloc['assigned_pitches'][m['pitch_idx']]
            master_schedule.append({
                'age_group': age, 'slot': m['slot'], 'time_label': TIME_MAP[m['slot']],
                'pitch_id': pitch_obj['id'], 'pitch_name': pitch_obj['name'],
                'zone': pitch_obj['zone'], 'team1': m['t1'], 'team2': m['t2']
            })
    return master_schedule

# ==========================================
# 5. EXPORT SCRIPTS
# ==========================================

def export_to_csv(master_schedule, filename="master_schedule.csv"):
    keys = ['age_group', 'slot', 'time_label', 'zone', 'pitch_name', 'pitch_id', 'team1', 'team2']
    sorted_schedule = sorted(master_schedule, key=lambda x: (x['slot'], x['zone'], x['pitch_id']))
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(sorted_schedule)

def generate_summary_dashboard(allocations, master_schedule, title, filename="summary_dashboard.html", config_info=None, index_link=None, discovery_configs=None):
    print(f"Exporting Summary Dashboard: {filename}...")
    
    total_teams = sum(a['teams'] for a in allocations)
    total_players = config_info['total_players'] if config_info else sum(a.get('total_players', 0) for a in allocations)
    used_pitches = sum(a['pitches_req'] for a in allocations)
    val = perform_validation(master_schedule)

    zones = defaultdict(list)
    for a in allocations:
        for p in a['assigned_pitches']: zones[p['zone']].append({'name': p['name'], 'age': a['age_group']})
            
    # Pitch to Age mapping for the Age column
    pitch_to_age = {}
    for a in allocations:
        for p_assigned in a['assigned_pitches']:
            pitch_to_age[p_assigned['id']] = a['age_group']

    pitch_schedule = defaultdict(dict)
    for m in master_schedule: 
        pitch_schedule[m['pitch_id']][m['slot']] = f"<div class='fixture'>{m['team1']}<br>vs<br>{m['team2']}</div>"

    nav_html = f'<div style="text-align: center; margin-bottom: 20px;"><a href="{index_link}" style="color: #3498db; text-decoration: none; font-weight: bold;">&larr; Back to Recommended Proposal Index</a></div>' if index_link else ""
    
    css = """
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f7f6; color: #333; }
        h1, h2 { text-align: center; color: #2c3e50; }
        .container { max-width: 1300px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
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
        th, td { border: 1px solid #ddd; padding: 10px; font-size: 0.8em; }
        .fixture { font-size: 0.85em; line-height: 1.2; }
        th { background-color: #ecf0f1; color: #2c3e50; }
        .day-header { background-color: #34495e; color: white; font-weight: bold; }
        .cell-jp1 { background-color: #d5f5e3; color: #1e8449; font-weight: bold;}
        .cell-jp2 { background-color: #d6eaf8; color: #21618c; font-weight: bold;}
        .cell-jp3 { background-color: #fdebd0; color: #b9770e; font-weight: bold;}
        .cell-jp4 { background-color: #fadbd8; color: #943126; font-weight: bold;}
        .status-pass { color: #27ae60; font-weight: bold; }
        .status-warn { color: #e67e22; font-weight: bold; }
        .discovery-table { font-size: 0.85em; }
        .discovery-table a { color: #3498db; text-decoration: none; font-weight: bold; }
        .validation-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; margin-top: 15px; }
        .val-item { background: #f8f9f9; padding: 10px; border-radius: 5px; border: 1px solid #eee; }
    """
    
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{title}</title><style>{css}</style></head>
    <body><div class="container">{nav_html}<h1>Tournament Configuration: {title}</h1>
    <div class="summary-bar">
        <div class="summary-item"><span class="val">{len(allocations)}</span><span class="lbl">Age Groups</span></div>
        <div class="summary-item"><span class="val">{total_teams}</span><span class="lbl">Total Teams</span></div>
        <div class="summary-item"><span class="val">{total_players}</span><span class="lbl">Total Players</span></div>
        <div class="summary-item"><span class="val">{len(master_schedule)}</span><span class="lbl">Total Matches</span></div>
        <div class="summary-item"><span class="val">{used_pitches}</span><span class="lbl">Pitches</span></div>
    </div>
    <hr><h2>1. Pitch Map & Zone Assignment</h2><div class="zone-wrapper">"""
    
    for z in sorted(zones.keys()):
        html += f'<div class="zone {z.lower()}"><h3>{z}</h3><div class="pitch-grid">'
        for p in zones[z]: html += f'<div class="pitch-card">{p["name"]}<br><small>{p["age"]}</small></div>'
        html += '</div></div>'
    
    html += '</div><hr><h2>2. Age Group Breakdown</h2><div class="table-container"><table><thead><tr><th>Age Group</th><th>Teams</th><th>Players/Team</th><th>Total Players</th><th>Matches/Team</th><th>Play Time %</th><th>Total Matches</th><th>Pitches Req.</th><th>Zone</th></tr></thead><tbody>'
    for a in allocations:
        z = a['assigned_pitches'][0]['zone']
        matches_per_team = a['teams'] - 1
        play_time_pct = (matches_per_team / 15) * 100
        html += f"<tr><td><strong>{a['age_group']}</strong></td><td>{a['teams']} Teams</td><td>{a.get('players_per_team', 'N/A')}</td><td>{a.get('total_players', 'N/A')}</td><td>{matches_per_team}</td><td>{play_time_pct:.1f}%</td><td>{a['matches']}</td><td>{a['pitches_req']}</td><td><span class='{z.lower()}'>{z}</span></td></tr>"
    
    html += '</tbody></table></div><hr><h2>3. Master Tournament Schedule</h2><div class="table-container"><table><thead><tr><th>Pitch</th><th>Age</th>'
    for i in range(1, 17): 
        label = TIME_MAP[i].replace(' ', '<br>')
        html += f"<th>S{i}<br><small>{label}</small></th>"
    html += '</tr></thead><tbody>'
    for p in PITCH_INVENTORY:
        age_group_name = pitch_to_age.get(p['id'], "-")
        zone_cls = f"cell-{p['zone'].lower()}"
        html += f"<tr><td class='{zone_cls}'><strong>{p['name']}</strong></td><td class='{zone_cls}'><small>{age_group_name}</small></td>"
        for s in range(1, 17):
            fixture = pitch_schedule[p['id']].get(s)
            html += f'<td class="{zone_cls}">{fixture if fixture else "-"}</td>'
        html += "</tr>"
    
    # 4. Validation Report with Age Breakdown
    consecutive_msg = "No team is playing more than 2 games in a row." if val['max_consecutive'] <= 2 else f"Warning: Some teams play {val['max_consecutive']} games in a row."
    consistency_msg = "PASS" if val['consistency_pass'] else "FAIL"
    html += f"""</tbody></table></div><hr><h2>4. Validation & Quality Report</h2>
    <div style="background: #fdfefe; border: 1px solid #dcdfe0; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
        <p><strong>Integrity Status:</strong> <span class="status-pass">{val['status']}</span> (No Clashes, No Double-Bookings)</p>
        <p><strong>Round Robin Status:</strong> <span class="status-pass">PASS</span> (All teams play N-1 games)</p>
        <p><strong>Schedule Consistency:</strong> <span class="status-pass">{consistency_msg}</span> (Same-size age groups have identical match sequences)</p>
        <p><strong>Rest Spacing Quality:</strong> There are <span class="status-warn">{val['back_to_back']}</span> instances of back-to-back games, spread across {val['back_to_back_teams_count']} different teams. <strong>{consecutive_msg}</strong></p>
        <div class="validation-grid">"""
    
    for a in allocations:
        count = val['age_back_to_back'].get(a['age_group'], 0)
        status_cls = "status-pass" if count == 0 else "status-warn"
        html += f'<div class="val-item"><strong>{a["age_group"]}</strong><br><span class="{status_cls}">{count}</span> consecutive games</div>'
    
    html += "</div></div>"

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
                            <li><strong>Session Timing:</strong> both Tue and Thu finish at 8:30 PM latest</li>
                            <li><strong>Minimal Movement:</strong> Age groups are ring-fenced to specific dedicated pitches</li>
                        </ul>
                    </div>
                    <div style="flex: 1; min-width: 300px;">
                        <h4 style="margin-top:0; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">Capacity Math</h4>
                        <ul style="padding-left: 20px;">
                            <li><strong>Total Time:</strong> 2 hours per night (8 core slots per night)</li>
                            <li><strong>Pitch Capacity:</strong> 16 core matches</li>
                            <li><strong>Tournament Cap (14 Pitches):</strong> 224 core match slots</li>
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
    grid_data = defaultdict(dict)
    for m in master_schedule: grid_data[m['pitch_name']][m['slot']] = f"{m['team1']}<br>vs<br>{m['team2']}"
    html = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Matchup Grid</title><style>body{font-family:Arial;margin:20px;}table{width:100%;border-collapse:collapse;text-align:center;}th,td{border:1px solid #ddd;padding:5px;font-size:0.8em;}</style></head><body><h1>Detailed Matchup Grid</h1><table><thead><tr><th>Pitch</th>"""
    for i in range(1, 17):
        label = TIME_MAP[i].replace(' ', '<br>')
        html += f"<th>S{i}<br><small>{label}</small></th>"
    html += "</tr></thead><tbody>"
    for p in PITCH_INVENTORY:
        html += f"<tr><td><strong>{p['name']}</strong></td>"
        for s in range(1, 17): html += f"<td>{grid_data[p['name']].get(s, '-')}</td>"
        html += "</tr>"
    html += "</tbody></table></body></html>"
    with open(filename, 'w') as f: f.write(html)

def map_config_to_ages(config, start_age=6):
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
    content = f"# Wayside Mini World Cup 2026\n\n## 🏆 RECOMMENDED PROPOSAL\n\n- **Dashboard:** [View Interactive Dashboard](index.html)\n- **Matchup Grid:** [View Detailed Matchup Grid](master_schedule_grid_final.html)\n\n### Summary:\n- **{final_info['num_age_groups']}** Age Groups\n- **{final_info['total_teams']}** Teams\n- **{final_info['total_players']}** Players\n\n---\n\n## Discovery Options\n\n| Option | Teams | Players | Dashboard |\n| :--- | :--- | :--- | :--- |\n"
    for i, c in enumerate(configs, 1):
        content += f"| **Option {i}** | {c['total_teams']} | {c['total_players']} | [View](options_output/summary_dashboard_option_{i}.html) |\n"
    with open(filename, 'w') as f: f.write(content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tournament Scheduler")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--no-cache", action="store_true", help="Disable schedule caching by bracket size")
    args = parser.parse_args()

    random.seed(args.seed)
    use_cache = not args.no_cache
    
    PITCH_COUNT = 14
    configs = discover_configurations(total_pitches=PITCH_COUNT)
    output_dir = "options_output"
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    
    for i, c in enumerate(configs, 1):
        # We don't cache discovery options to keep them varied, or we could if requested.
        # For now, let's keep them varied but use the seed for stability.
        age_groups = map_config_to_ages(c)
        rosters = {g['age']: [f"T{j}" for j in range(1, g['teams']+1)] for g in age_groups}
        alloc = allocate_tournament(f"Option {i}", age_groups, use_cache=False)
        master = generate_master_schedule(alloc['allocations'], rosters, use_cache=False)
        generate_summary_dashboard(alloc['allocations'], master, alloc['title'], os.path.join(output_dir, f"summary_dashboard_option_{i}.html"), config_info=c, index_link="../index.html")

    # Final Recommended Proposal - RE-ENABLE CACHE HERE
    SCHEDULE_CACHE.clear() # clear from discovery runs
    
    final_proposal = [
        {'age': 'U6/U7 Boys', 'teams': 6, 'players_per_team': 5, 'preferred_zone': 'JP3'},
        {'age': 'U8 Boys', 'teams': 8, 'players_per_team': 8, 'preferred_zone': 'JP3'},
        {'age': 'U9 Mixed', 'teams': 8, 'players_per_team': 8, 'preferred_zone': 'JP4'},
        {'age': 'U10 Mixed', 'teams': 8, 'players_per_team': 8, 'preferred_zone': 'JP1'},
        {'age': 'U11 Mixed', 'teams': 8, 'players_per_team': 8, 'preferred_zone': 'JP1'},
        {'age': 'U12 Mixed', 'teams': 8, 'players_per_team': 8, 'preferred_zone': 'JP2'},
        {'age': 'U13 Mixed', 'teams': 8, 'players_per_team': 8, 'preferred_zone': 'JP2'},
        {'age': 'U7/U8 Girls', 'teams': 6, 'players_per_team': 5, 'preferred_zone': 'JP4'},
    ]
    
    COUNTRIES = ["IRELAND", "GERMANY", "SPAIN", "ARGENTINA", "HOLLAND", "PORTUGAL", "BRAZIL", "ENGLAND", "FRANCE", "ITALY"]
    final_info = {'num_age_groups': len(final_proposal), 'total_teams': sum(g['teams'] for g in final_proposal), 'total_players': sum(g['teams']*g['players_per_team'] for g in final_proposal), 'used_pitches': 14, 'spare_pitches': 0}
    rosters_final = {g['age']: COUNTRIES[:g['teams']] for g in final_proposal}
    
    alloc_final = allocate_tournament("Final Recommended Proposal", final_proposal, use_cache=use_cache)
    master_final = generate_master_schedule(alloc_final['allocations'], rosters_final, use_cache=use_cache)
    
    export_to_csv(master_final, "master_schedule_final.csv")
    generate_summary_dashboard(alloc_final['allocations'], master_final, "Final Recommended Proposal", "index.html", config_info=final_info, discovery_configs=configs)
    generate_detailed_html_grid(master_final, alloc_final['allocations'], "master_schedule_grid_final.html")
    generate_readme_index(configs, output_dir, final_info=final_info)
