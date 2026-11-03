# JASS Active 65+

Offline desktop health and fitness tracker using Python, PySide6 and SQLite.

## Included
Dashboard, profile, fitness/strength logging, food/protein logging, supplement register, private men's vitality tracking, historical lab records, health trends, appointments, CSV export and SQLite backup.

## Run on Windows
1. Install Python 3.10+ from https://www.python.org/downloads/
2. Double-click `run_windows.bat`, or open Command Prompt in this folder and run:
   `py -m pip install PySide6`
   `py jass_active65.py`

## Run on Debian / MX Linux / Ubuntu
Run `chmod +x run_linux.sh` then `./run_linux.sh`, or install PySide6 with your package manager and run `python3 jass_active65.py`.
No virtual environment is required by the application.

## Data
The database is created at `data/jass_active65.sqlite3` on first launch. Use Reports & Backup to export CSVs or create a backup. Keep this file private.

## Historical health records
The profile uses the supplied details: age 65, height 182.9 cm, weight 75 kg, moderately active, vegetarian including eggs/dairy. Historical laboratory values are seeded from the previously supplied reports. The February 21, 2025 date is applied only where that date was visible in the report. Where a report image did not show its date, the date is left blank. The lipid report date is also left blank because it was not confirmed in the image. New results are appended; old results are not overwritten.

## Important
This is a personal record-keeping tool, not a medical diagnostic or prescribing system. Historical LDL 186.88 mg/dL and triglycerides 212.99 mg/dL warrant updated testing and clinician review. The previous CBC's low MCH/MCHC warrants discussion of ferritin/iron studies before taking iron. The prior kidney panel did not include eGFR or urine ACR. The provisional protein target should be reviewed against current kidney function and clinician advice.
