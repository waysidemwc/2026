import itertools
import os

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
    """6 Teams, 1 Pitch, 15 Matches."""
    print(f"--- Scheduling 6 Teams (1 Pitch) ---")
    rounds = generate_round_robin(teams)
    all_matches = [match for round_matches in rounds for match in round_matches]
    
    scheduled = []
    remaining = all_matches[:]
    
    while remaining:
        best_match = None
        best_score = -1
        
        for match in remaining:
            t1, t2 = match
            last_played_1 = -1
            last_played_2 = -1
            for i in range(len(scheduled)-1, -1, -1):
                if t1 in scheduled[i]: last_played_1 = i; break
            for i in range(len(scheduled)-1, -1, -1):
                if t2 in scheduled[i]: last_played_2 = i; break
            
            dist1 = len(scheduled) - last_played_1 if last_played_1 != -1 else 100
            dist2 = len(scheduled) - last_played_2 if last_played_2 != -1 else 100
            
            min_dist = min(dist1, dist2)
            if min_dist > best_score:
                best_score = min_dist
                best_match = match
                
        scheduled.append(best_match)
        remaining.remove(best_match)

    slot = 1
    for match in scheduled:
        print(f"Slot {slot:02d} (Pitch 1): {match[0]} vs {match[1]}")
        slot += 1
        if slot == 16:
             print("Slot 16 (Pitch 1): GLOBAL BREAK")
    print("\n")

def schedule_8_teams(teams):
    """8 Teams, 2 Pitches, 28 Matches."""
    print(f"--- Scheduling 8 Teams (2 Pitches) ---")
    rounds = generate_round_robin(teams)
    
    slot = 1
    for round_num, round_matches in enumerate(rounds):
        print(f"Slot {slot:02d} | Pitch 1: {round_matches[0][0]} vs {round_matches[0][1]} | Pitch 2: {round_matches[1][0]} vs {round_matches[1][1]}")
        slot += 1
        print(f"Slot {slot:02d} | Pitch 1: {round_matches[2][0]} vs {round_matches[2][1]} | Pitch 2: {round_matches[3][0]} vs {round_matches[3][1]}")
        slot += 1
        
        if slot == 11 or slot == 14:
            print(f"Slot {slot:02d} | GLOBAL BREAK (Both Pitches)")
            slot += 1
    print("\n")

def schedule_10_teams(teams):
     """10 Teams, 3 Pitches, 45 Matches."""
     print(f"--- Scheduling 10 Teams (3 Pitches) ---")
     rounds = generate_round_robin(teams)
     all_matches = [match for round_matches in rounds for match in round_matches]
     
     slot = 1
     for i in range(0, len(all_matches), 3):
         matches_in_slot = all_matches[i:i+3]
         output = f"Slot {slot:02d} | "
         for j, match in enumerate(matches_in_slot):
             output += f"Pitch {j+1}: {match[0]:>2} vs {match[1]:>2} | "
         print(output.strip(" | "))
         slot += 1
     print("\n")


# ==========================================
# 2. ALLOCATION & RESOURCE MANAGEMENT
# ==========================================

PITCH_INVENTORY = [
    {'id': 'P1', 'name': 'Pitch 1', 'zone': 'JP1'},
    {'id': 'P2', 'name': 'Pitch 2', 'zone': 'JP1'},
    {'id': 'P3', 'name': 'Pitch 3', 'zone': 'JP1'},
    {'id': 'P4', 'name': 'Pitch 4', 'zone': 'JP1'},
    {'id': 'P5', 'name': 'Pitch 5', 'zone': 'JP2'},
    {'id': 'P6', 'name': 'Pitch 6', 'zone': 'JP2'},
    {'id': 'P7', 'name': 'Pitch 7', 'zone': 'JP2'},
    {'id': 'P8', 'name': 'Pitch 8', 'zone': 'JP2'},
    {'id': 'P9', 'name': 'Pitch 9', 'zone': 'JP3'},
    {'id': 'P10', 'name': 'Pitch 10', 'zone': 'JP3'},
    {'id': 'P11', 'name': 'Pitch 11', 'zone': 'JP3'},
    {'id': 'P12', 'name': 'Pitch 12', 'zone': 'JP4'},
    {'id': 'P13', 'name': 'Pitch 13', 'zone': 'JP4'},
    {'id': 'P14', 'name': 'Pitch 14', 'zone': 'JP4'},
]

def get_requirements(team_count):
    """Calculates required matches and pitches based on team count."""
    if team_count <= 6:
        return 15, 1
    elif team_count <= 8:
        return 28, 2
    elif team_count <= 10:
        return 45, 3
    else:
        raise ValueError("Team count must be 6, 8, or 10 for optimal pitch usage.")

def allocate_tournament(option_name, age_groups):
    """Assigns available pitches to age groups based on their requirements."""
    print(f"Allocating Pitches for {option_name}...")
    
    available_pitches = PITCH_INVENTORY.copy()
    allocations = []
    
    total_teams = 0
    total_matches = 0
    
    for group in age_groups:
        name = group['age']
        teams = group['teams']
        
        matches, pitches_needed = get_requirements(teams)
        total_teams += teams
        total_matches += matches
        
        if len(available_pitches) < pitches_needed:
            print(f"ERROR: Not enough pitches left to allocate {name} ({pitches_needed} needed).")
            break
            
        # Assign pitches
        assigned = []
        for _ in range(pitches_needed):
            assigned.append(available_pitches.pop(0))
            
        allocations.append({
            'age_group': name,
            'teams': teams,
            'matches': matches,
            'pitches_req': pitches_needed,
            'assigned_pitches': assigned
        })
        
    return {
        'title': option_name,
        'summary': f"{total_teams} Teams | {total_matches} Matches | {14 - len(available_pitches)} Pitches Used",
        'allocations': allocations,
        'remaining_pitches': available_pitches
    }

# ==========================================
# 3. HTML VISUALIZATION GENERATOR
# ==========================================

def generate_html_visualization(data, filename="tournament_allocation.html"):
    """Generates an HTML file containing the table and zone visualization."""
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{data['title']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f4f7f6; color: #333; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            h1, h2 {{ text-align: center; color: #2c3e50; }}
            table {{ width: 100%; border-collapse: collapse; text-align: center; margin-bottom: 30px; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; }}
            th {{ background-color: #ecf0f1; color: #2c3e50; }}
            .zone-jp1 {{ color: #27ae60; font-weight: bold; }}
            .zone-jp2 {{ color: #2980b9; font-weight: bold; }}
            .zone-jp3 {{ color: #e67e22; font-weight: bold; }}
            .zone-jp4 {{ color: #c0392b; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{data['title']}</h1>
            <p style="text-align: center;"><strong>{data['summary']}</strong></p>
            <hr>
            <h2>Age Group Breakdown & Pitch Assignments</h2>
            <table>
                <thead>
                    <tr>
                        <th>Age Group</th>
                        <th>Teams</th>
                        <th>Total Matches</th>
                        <th>Pitches Required</th>
                        <th>Dedicated Pitches</th>
                        <th>Zone</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Generate Table Rows
    for alloc in data['allocations']:
        pitch_names = ", ".join([p['name'] for p in alloc['assigned_pitches']])
        
        # Determine primary zone (assume all pitches for an age group are in the same zone for simplicity)
        primary_zone = alloc['assigned_pitches'][0]['zone']
        zone_class = f"zone-{primary_zone.lower()}"
        
        html_content += f"""
                    <tr>
                        <td><strong>{alloc['age_group']}</strong></td>
                        <td>{alloc['teams']}</td>
                        <td>{alloc['matches']}</td>
                        <td>{alloc['pitches_req']}</td>
                        <td>{pitch_names}</td>
                        <td class="{zone_class}">{primary_zone}</td>
                    </tr>
        """
        
    html_content += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    with open(filename, 'w') as f:
        f.write(html_content)
    print(f"Visualization successfully written to {filename}")


# ==========================================
# 4. EXECUTION
# ==========================================
if __name__ == "__main__":
    
    # Define Tournament Option 1
    option_1_config = [
        {'age': 'U6', 'teams': 6},
        {'age': 'U7', 'teams': 6},
        {'age': 'U8', 'teams': 6},
        {'age': 'U9', 'teams': 6},
        {'age': 'U10', 'teams': 8},
        {'age': 'U11', 'teams': 8},
        {'age': 'U12', 'teams': 10},
        {'age': 'U13', 'teams': 10},
    ]
    
    # Process allocations
    allocation_data = allocate_tournament("Option 1: The Full Spectrum", option_1_config)
    
    # Generate HTML File
    generate_html_visualization(allocation_data, "generated_allocations.html")
    
    # Optional: Run the schedule generators to output the match lists to console
    print("\nGenerating Sample Match Sequences...")
    # schedule_6_teams([f"Team{i}" for i in range(1, 7)])
    # schedule_8_teams([f"Team{i}" for i in range(1, 9)])
    # schedule_10_teams([f"Team{i}" for i in range(1, 11)])