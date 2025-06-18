# Tournament Analysis Scripts

This repository contains scripts for analyzing tournament data, comparing player registrations, and validating fixtures between years.

## Prerequisites

- Python 3.7+
- pandas library (`pip install pandas`)

## Data Structure

The scripts expect TSV (tab-separated values) files in the `data_in/` directory with the following structure:

### Player Analysis Files
- `mwc_2025_teams_export.tsv` - Main team assignments file
- `mwc_2025_teams_u14 - MattSheetu{age}.tsv` - Registration files for each age group (u7, u8, u10, u12, u14)

### Fixture Analysis Files
- `mwc_2025_teams_u14 - 2024_scoresheet{age}.tsv` - 2024 fixture files for each age group
- `mwc_2025_teams_u14 - app_fixtures.tsv` - 2025 fixture file (all age groups)

## Scripts

### 1. Check Players in App against Registration

Analyzes player data across all age groups to ensure consistency between team assignments and registrations.

```bash
python check_players_in_matt_and_app.py 
```

**Features:**
- **Duplicate Detection**: Finds players with duplicate names across all age groups
- **Multi-Age Analysis**: Compares all age groups (U7, U8, U10, U12, U14) simultaneously
- **Country Validation**: Verifies players are assigned to correct countries
- **Comprehensive Reporting**: Shows counts by age group and detailed mismatch analysis

**Output:**
- Console summary with duplicate players and statistics
- Detailed analysis of country assignment errors
- Player counts by age group and country

**Key Checks:**
- Players appearing multiple times across age groups
- Country mismatches between team assignments and registrations
- Missing players in either team assignments or registrations
- Duplicate registrations within age groups

### 2. Check Fixtures

Compares 2024 and 2025 fixtures to ensure tournament structure consistency, accounting for venue changes and date normalization.

```bash
python ./check_fixtures_2025v2024.py 
```

**Venue Remapping (Automatically Applied):**
The script automatically applies these pitch remappings when comparing 2024 to 2025:
- 2024 Pitch JP1.2 → 2025 Field JP1.3
- 2024 Pitch JP1.3 → 2025 Field JP1.4
- 2024 Pitch JP2.4 → 2025 Field JP4.3
- 2024 Pitch JP1.4 → 2025 Field JP1.2

**Features:**
- **Multi-Day Tournament Support**: Normalizes dates to "day1"/"day2" for comparison
- **Venue Remapping**: Automatically applies known pitch changes between years
- **Comprehensive Analysis**: Compares time, teams, and venues across all age groups
- **Markdown Reports**: Generates detailed reports in `data_out/` directory

**Output:**
- Console summary showing matches and mismatches by age group
- Timestamped markdown report with detailed analysis
- Pitch/field mismatch identification
- Missing fixture analysis

**Key Checks:**
- Fixture time consistency between years
- Team matchup validation
- Venue assignment accuracy (with remapping)
- Tournament structure changes
- Two-day tournament format preservation

## Output Files

Both scripts generate output in the `data_out/` directory:
- Markdown reports with timestamped filenames
- Detailed analysis tables
- Recommendations for resolving issues

## Date Handling

The fixture comparison script handles multi-day tournaments by normalizing dates:
- **2024**: `2024-06-11` becomes `day1`, `2024-06-13` becomes `day2`
- **2025**: `06-10-2025` becomes `day1`, `06-12-2025` becomes `day2`

This ensures proper matching of corresponding tournament days regardless of actual calendar dates.

## Troubleshooting

### Common Issues

1. **File Not Found**: Ensure all required TSV files are in the `data_in/` directory
2. **Encoding Issues**: Files should be UTF-8 encoded
3. **Column Mismatches**: Verify TSV files have the expected column headers
4. **Empty Results**: Check that data files contain the expected age group formats (U7, U8, etc.)

### Expected File Formats

**Team Export File:**
```
Age	Name	Country	Players	Manager
U14	ARGENTINA	AR	PLAYER1, PLAYER2, PLAYER3	
```

**Registration Files:**
```
Registration Number	DOB	Gender	First Name Last Name	Team #	Team Manager	Country
MANUAL ENTRY	04/01/2011	Male	JOHN SMITH	Team 3		IRELAND
```

**Fixture Files:**
```
Time	Goals Team1	Goals Team2	Pitch	Team1	Team2
2024-06-11 18:30	0	0	JP1.4	IRELAND u7	GERMANY u7
```

## Contact

For issues or questions about these scripts, please check the generated reports in `data_out/` first, as they contain detailed analysis and recommendations for resolving any identified problems.