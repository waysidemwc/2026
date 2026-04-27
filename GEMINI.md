# Gemini Context: Wayside Mini World Cup 2026

This project is a tournament scheduling and configuration system for the Wayside Mini World Cup 2026. It autonomously generates, validates, and visualizes multi-pitch, multi-age-group soccer tournaments.

## Project Overview

The system handles the complexity of scheduling for multiple age groups across 14 dedicated pitches, organized into four geographical zones (JP1 to JP4). It prioritizes "ring-fencing" age groups to specific pitches to minimize player and parent movement.

### Core Architecture
- **Scheduling Engine:** `scripts/tournament_scheduler.py` uses a Monte-Carlo Greedy approach to optimize team rest intervals and ensure valid round-robin brackets (6, 8, or 10 teams).
- **Validation Suite:** `scripts/validate_schedule.py` performs exhaustive checks for team clashes, pitch double-bookings, and round-robin integrity.
- **Static Site Generation:** The system exports interactive HTML dashboards and detailed matchup grids for visual inspection and deployment to GitHub Pages.

## Building and Running

### Prerequisites
- Python 3.x
- Virtual environment (recommended): `source env/bin/activate` or `source venv/bin/activate`

### Key Commands
- **Regenerate Entire Tournament:**
  ```bash
  python3 scripts/tournament_scheduler.py
  ```
  This script explores all valid configurations, generates the recommended proposal (`index.html`), and populates `options_output/` with alternatives.

- **Validate a Schedule:**
  ```bash
  python3 scripts/validate_schedule.py master_schedule_final.csv
  ```

## Development Conventions

### Pitch & Zone Mapping
The project uses a strict zone-based allocation strategy:
- **JP1:** U10 Mixed, U11 Mixed
- **JP2:** U12 Mixed, U13 Mixed
- **JP3:** U8 Boys, U6/U7 Boys
- **JP4:** U9 Mixed, U7/U8 Girls

### Data Structures
- **CSV Format:** The master schedule is exported with headers: `age_group, slot, time_label, zone, pitch_name, pitch_id, team1, team2`.
- **Slot Timing:** Matches are 12 minutes with a 3-minute gap (15-minute slots). Core sessions run on Tuesday and Thursday evenings, concluding by 8:30 PM latest.

### Visual Standards
- Dashboard colors are synchronized with the JP pitch zones:
  - **JP1:** Green (`#27ae60`)
  - **JP2:** Blue (`#2980b9`)
  - **JP3:** Orange (`#e67e22`)
  - **JP4:** Red (`#c0392b`)

## Git Configuration

- **Remote Access:** The repository is configured to use SSH for authentication (`git@github.com:waysidemwc/2026.git`).
- **GitHub Pages:** The `main` branch is used to push updates to the `pages` branch for hosting.
