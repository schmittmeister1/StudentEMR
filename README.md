# PTA EMR Playground (100-Patient Mixed Caseload)

Educational EMR-style “playground” for PTA students (Flask + SQLite).  
**All data is synthetic** and intended for skills practice (documentation, chart review, billing/time tracking, etc.).

## What’s Included
- **100 unique patient charts** (no shared first or last names)
- Mixed outpatient caseload:
  - Orthopedic
  - Sports
  - Neurological
  - Geriatric / fall risk
  - Pediatrics
  - Vestibular
  - Pelvic Health
- Documentation templates:
  - **Evaluation**
  - **Daily Visit Note**
  - **Progress Report**
  - **Discharge Summary**
- Each template contains structured sections aligned to common Medicare-style documentation expectations (date, history, tests/measures, goals, POC, signatures, etc.).
- **Charges module** with CPT codes, minutes, units, and totals (for teaching purposes).

## Default Logins
- **Faculty / Instructor**
  - Email: `instructor@pta.local`
  - Password: `instructor123`
- **Student**
  - Email: `student1@pta.local`
  - Password: `student123`
- **Student**
  - Email: `student2@pta.local`
  - Password: `student123`

## Run (Windows / Mac / Linux)

### Option A — Standard (recommended)
1. Install Python 3.10+ (3.11/3.12 works).
2. Open a terminal in the project folder (the folder containing `app.py`).
3. Create and activate a virtual environment:

**Windows (PowerShell or CMD)**
```bat
python -m venv .venv
.venv\Scripts\activate
```

**Mac/Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

4. Install requirements:
```bash
pip install -r requirements.txt
```

5. Run:
```bash
python app.py
```

6. Open your browser to:
- http://127.0.0.1:5000

### Option B — “One-click” scripts
- Windows: double-click `run_windows.bat`
- Mac/Linux: run `./run_mac_linux.sh`

## Reset / Reseed the Database
The app uses SQLite at `instance/emr.sqlite`.

### Reset inside the app
1. Log in as instructor.
2. Go to **Admin**.
3. Click **Reset & Reseed**.

### Reset manually
1. Stop the server (CTRL+C).
2. Delete the `instance/emr.sqlite` file.
3. Start the app again.

## Notes
- This is a teaching application. Do **not** deploy publicly or use with real patient data.
- CPT/unit calculation is an educational approximation; real billing rules may differ by payer and scenario.
