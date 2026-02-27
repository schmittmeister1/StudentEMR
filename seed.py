from __future__ import annotations

import random
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Tuple, Optional

from werkzeug.security import generate_password_hash

from extensions import db
from models import User, Patient, Allergy, Medication, Problem, Encounter, Note, Charge, Appointment


def ensure_seed_data(force: bool = False) -> None:
    """Seed the database with 100 synthetic outpatient cases.

    - Unique first AND last names across all patients (no duplicates).
    - Mixed caseload: Orthopedic, Neurological, Geriatric, Sports, Pediatrics, Vestibular, Pelvic Health.
    - Mix of new patients (Eval only) and established patients (Eval + multiple visits + Progress, some Discharge).

    IMPORTANT: All data is synthetic for training only.
    """
    if not force and User.query.first():
        return

    random.seed(42)

    # -------------------------
    # Users
    # -------------------------
    instructor = User(
        email="instructor@pta.local",
        name="Alex Morgan",
        role="instructor",
        credentials="PT, DPT",
        license_number="PT12345",
        password_hash=generate_password_hash("instructor123"),
    )
    student1 = User(
        email="student1@pta.local",
        name="Jordan Lee",
        role="student",
        credentials="PTA-S",
        license_number=None,
        password_hash=generate_password_hash("student123"),
    )
    student2 = User(
        email="student2@pta.local",
        name="Taylor Chen",
        role="student",
        credentials="PTA-S",
        license_number=None,
        password_hash=generate_password_hash("student123"),
    )
    db.session.add_all([instructor, student1, student2])
    db.session.flush()

    providers = [instructor, student1, student2]

    # -------------------------
    # Synthetic name pool
    # (100 unique first + 100 unique last)
    # -------------------------
    first_names = [
        "Adrian","Bianca","Caleb","Daphne","Elias","Farah","Gavin","Helena","Iris","Jonah",
        "Keira","Liam","Maya","Nolan","Olivia","Priya","Quentin","Raina","Soren","Talia",
        "Uriah","Valeria","Wesley","Ximena","Yusuf","Zara","Amir","Brielle","Carmen","Dario",
        "Elena","Felix","Gianna","Hector","Ismael","Jocelyn","Khalil","Leona","Mateo","Noelle",
        "Omar","Penelope","Rafael","Selene","Tomas","Uma","Violet","Wyatt","Xander","Yara",
        "Zane","Aisha","Brandon","Cassidy","Declan","Esme","Franco","Greta","Hannah","Imani",
        "Jasper","Kendall","Logan","Marisol","Naomi","Orion","Paola","Reed","Sabrina","Tristan",
        "Ulysses","Veronica","Willa","Xavier","Yvette","Zion","Anya","Bennett","Colette","Dominic",
        "Emerson","Fiona","Grant","Harper","Indira","Julian","Kara","Lucia","Micah","Nia",
        "Owen","Parker","Rosa","Samir","Teagan","Ulani","Vivian","Winter","Xiavier","Yesenia",
    ]
    last_names = [
        "Alden","Barrett","Caldwell","Delacroix","Eastman","Fairchild","Gallagher","Hargrove","Iverson","Jamison",
        "Kensington","Langford","Montgomery","Nightingale","Oakley","Prescott","Quill","Rutherford","Sinclair","Thatcher",
        "Underwood","Vandermeer","Whitaker","Xu","Youngblood","Zimmerman","Archer","Bramwell","Corwin","Donovan",
        "Ellington","Fitzpatrick","Grantham","Hollister","Ingram","Kaufman","Llewellyn","Merriweather","Northcott","O'Shea",
        "Pereira","Quintero","Rosenfeld","Santiago","Treadwell","Ulrich","Valentine","Winslow","Xiong","Yamamoto",
        "Zabinski","Atwood","Beaumont","Callahan","Davenport","Everhart","Farnsworth","Gaines","Hendrix","Iannone",
        "Jefferson","Kline","Laramie","Moreau","Nakamura","Olivetti","Pemberton","Quade","Ramos","Sheffield",
        "Templeton","Usher","Vasquez","Wainwright","Xue","Yeats","Zuniga","Ashford","Bancroft","Carmichael",
        "Driscoll","Echeverria","Feldman","Goodwin","Harrington","Iskander","Johansson","Kendrick","Leopold","Marquez",
        "Novak","Okafor","Parsons","Quinlan","Redmond","Sawyer","Townsend","Upton","Villarreal","Westbrook",
    ]

    # -------------------------
    # Referring physicians (synthetic)
    # -------------------------
    referring_physicians = [
        ("Morgan Fields, MD", "555-0101"),
        ("Casey Patel, DO", "555-0102"),
        ("Renee Alvarez, MD", "555-0103"),
        ("Samuel Brooks, MD", "555-0104"),
        ("Ivy Chen, MD", "555-0105"),
        ("Noah Bennett, DO", "555-0106"),
        ("Amina Hassan, MD", "555-0107"),
        ("Peter Nguyen, MD", "555-0108"),
        ("Elisa Romero, MD", "555-0109"),
        ("Dylan Price, DO", "555-0110"),
    ]

    # -------------------------
    # Insurance (synthetic)
    # -------------------------
    insurance_plans = [
        ("Medicare", "Medicare Part B", "Medicare"),
        ("UnitedHealthcare", "Choice Plus PPO", "Commercial"),
        ("Blue Cross Blue Shield", "PPO BlueOptions", "Commercial"),
        ("Aetna", "Open Access Managed Choice", "Commercial"),
        ("Cigna", "Connect Network", "Commercial"),
        ("Humana", "Gold Plus HMO", "Commercial"),
        ("Tricare", "Tricare Prime", "Tricare"),
        ("Medicaid", "State Medicaid", "Medicaid"),
    ]

    # -------------------------
    # Case templates (synthetic ICD-10)
    # Each template produces unique chart content via small variations.
    # -------------------------
    def ortho_templates() -> List[Dict[str, Any]]:
        return [
            {
                "title": "Lumbar radiculopathy",
                "medical_dx": "M54.16 - Radiculopathy, lumbar region",
                "treatment_dx": "M62.81 - Muscle weakness (generalized); R26.2 - Difficulty in walking; M54.50 - Low back pain",
                "outcomes": {"Oswestry": (28, 10)},  # baseline %, expected improvement
                "precautions": "prec: monitor s/s neuro changes; avoid provocative positions early; progress as tol.",
                "contra": "contra: red flag s/s (bowel/bladder changes, saddle anesthesia) -> refer.",
                "cpt_plan": ["97110", "97112", "97530", "97140", "97535"],
            },
            {
                "title": "Rotator cuff tendinopathy",
                "medical_dx": "M75.41 - Impingement syndrome of right shoulder",
                "treatment_dx": "M25.511 - Pain in right shoulder; M62.81 - Muscle weakness; M25.611 - Stiffness of right shoulder",
                "outcomes": {"NDI": None, "LEFS": None},
                "precautions": "prec: avoid impingement positions; pain-guided ROM; posture education.",
                "contra": "contra: acute trauma w/ deformity; progressive neuro deficit.",
                "cpt_plan": ["97110", "97112", "97140", "97530", "97535"],
            },
            {
                "title": "Post-op TKA",
                "medical_dx": "Z96.651 - Presence of right artificial knee joint (s/p R TKR)",
                "treatment_dx": "M25.561 - Pain in right knee; M25.661 - Stiffness of right knee; R26.2 - Difficulty in walking",
                "outcomes": {"LEFS": (32, 15)},
                "precautions": "prec: monitor incision/edema; WBAT per MD; ROM goals per protocol.",
                "contra": "contra: s/s DVT, wound infection -> urgent eval.",
                "cpt_plan": ["97110", "97116", "97530", "97140", "97535"],
            },
            {
                "title": "Cervical radiculopathy",
                "medical_dx": "M54.12 - Radiculopathy, cervical region",
                "treatment_dx": "M54.2 - Cervicalgia; M62.81 - Muscle weakness; R29.3 - Abnormal posture",
                "outcomes": {"NDI": (34, 14)},
                "precautions": "prec: monitor neuro s/s; avoid sustained provocation; posture + ergonomics.",
                "contra": "contra: vertebrobasilar insufficiency red flags; unexplained neuro decline.",
                "cpt_plan": ["97110", "97112", "97140", "97530", "97535"],
            },
        ]

    def sports_templates() -> List[Dict[str, Any]]:
        return [
            {
                "title": "Lateral ankle sprain",
                "medical_dx": "S93.401D - Sprain of unspecified ligament of right ankle, subsequent encounter",
                "treatment_dx": "M25.571 - Pain in right ankle; M62.81 - Muscle weakness; R26.89 - Other abnormalities of gait",
                "outcomes": {"LEFS": (48, 12)},
                "precautions": "prec: protect ligament healing; progress WB/plyo per tolerance; brace PRN.",
                "contra": "contra: suspected fx per Ottawa rules -> refer.",
                "cpt_plan": ["97110", "97112", "97116", "97530", "97535"],
            },
            {
                "title": "ACL reconstruction (mid rehab)",
                "medical_dx": "Z98.890 - Other specified postprocedural states (s/p ACLR)",
                "treatment_dx": "M25.561 - Pain in right knee; M62.81 - Muscle weakness; R26.2 - Difficulty in walking",
                "outcomes": {"LEFS": (38, 18)},
                "precautions": "prec: follow ACL protocol; avoid valgus collapse; monitor effusion.",
                "contra": "contra: acute swelling/warmth, fever, calf pain -> medical eval.",
                "cpt_plan": ["97110", "97112", "97530", "97116"],
            },
            {
                "title": "Patellofemoral pain (runner)",
                "medical_dx": "M22.2X1 - Patellofemoral disorders, right knee",
                "treatment_dx": "M25.561 - Pain in right knee; M62.81 - Muscle weakness; R29.3 - Abnormal posture",
                "outcomes": {"LEFS": (56, 10)},
                "precautions": "prec: load management; avoid pain escalation >2 points; cadence/hip control cues.",
                "contra": "contra: traumatic instability event -> refer.",
                "cpt_plan": ["97110", "97112", "97530", "97535"],
            },
        ]

    def neuro_templates() -> List[Dict[str, Any]]:
        return [
            {
                "title": "CVA - hemiparesis",
                "medical_dx": "I69.354 - Hemiplegia and hemiparesis following cerebral infarction affecting left dominant side",
                "treatment_dx": "R26.81 - Unsteadiness on feet; M62.81 - Muscle weakness; Z91.81 - Hx of falling",
                "outcomes": {"Berg": (41, 8), "TUG": (15.8, -3.0)},
                "precautions": "prec: fall risk; monitor BP; gait belt; consider AFO per needs.",
                "contra": "contra: uncontrolled HTN, chest pain, acute neuro change -> stop and refer.",
                "cpt_plan": ["97112", "97116", "97530", "97535"],
            },
            {
                "title": "Parkinson's disease (balance & gait)",
                "medical_dx": "G20 - Parkinson's disease",
                "treatment_dx": "R26.81 - Unsteadiness on feet; R26.89 - Other gait abnormalities; M62.81 - Muscle weakness",
                "outcomes": {"Berg": (44, 6), "TUG": (13.2, -2.0)},
                "precautions": "prec: fall risk; monitor fatigue; cueing for amplitude; home safety.",
                "contra": "contra: orthostatic hypotension symptomatic -> modify session.",
                "cpt_plan": ["97112", "97116", "97530", "97535"],
            },
            {
                "title": "Peripheral neuropathy (DM)",
                "medical_dx": "G62.9 - Polyneuropathy, unspecified",
                "treatment_dx": "R26.81 - Unsteadiness on feet; M62.81 - Muscle weakness; R20.2 - Paresthesia of skin",
                "outcomes": {"Berg": (39, 9)},
                "precautions": "prec: foot inspection; fall risk; monitor blood glucose PRN.",
                "contra": "contra: open wound/skin breakdown -> refer to wound care.",
                "cpt_plan": ["97112", "97116", "97530", "97535"],
            },
        ]

    def geriatric_templates() -> List[Dict[str, Any]]:
        return [
            {
                "title": "Deconditioning post hospitalization",
                "medical_dx": "R53.81 - Other malaise (deconditioning)",
                "treatment_dx": "M62.81 - Muscle weakness; R26.81 - Unsteadiness; Z91.81 - Hx of falling",
                "outcomes": {"Berg": (36, 10), "TUG": (18.4, -4.0)},
                "precautions": "prec: monitor VS (BP/HR/SpO2); energy conservation; fall risk.",
                "contra": "contra: SpO2 < 88% persistent or CP -> stop and refer.",
                "cpt_plan": ["97110", "97112", "97116", "97530", "97535"],
            },
            {
                "title": "Repeated falls / balance impairment",
                "medical_dx": "R29.6 - Repeated falls",
                "treatment_dx": "R26.81 - Unsteadiness on feet; M62.81 - Muscle weakness; Z91.81 - Hx of falling",
                "outcomes": {"Berg": (34, 12), "TUG": (20.1, -5.0)},
                "precautions": "prec: fall risk; assistive device training; home safety review.",
                "contra": "contra: syncope episodes not evaluated -> refer.",
                "cpt_plan": ["97112", "97116", "97530", "97535"],
            },
            {
                "title": "OA knee - gait limitation",
                "medical_dx": "M17.11 - Unilateral primary osteoarthritis, right knee",
                "treatment_dx": "M25.561 - Pain in right knee; M62.81 - Muscle weakness; R26.2 - Difficulty in walking",
                "outcomes": {"LEFS": (42, 12)},
                "precautions": "prec: load management; monitor effusion; avoid flare-ups >24 hrs.",
                "contra": "contra: acute hot swollen joint w/ fever -> medical eval.",
                "cpt_plan": ["97110", "97116", "97530", "97140", "97535"],
            },
        ]

    def pediatrics_templates() -> List[Dict[str, Any]]:
        return [
            {
                "title": "Gross motor delay",
                "medical_dx": "R62.0 - Delayed milestone in childhood",
                "treatment_dx": "R27.8 - Other lack of coordination; M62.81 - Muscle weakness",
                "outcomes": {"PedsQL": (58, 10)},
                "precautions": "prec: caregiver education; age-appropriate play; monitor fatigue.",
                "contra": "contra: acute illness/fever -> defer.",
                "cpt_plan": ["97530", "97110", "97535"],
            },
            {
                "title": "Cerebral palsy (ambulatory) - balance",
                "medical_dx": "G80.9 - Cerebral palsy, unspecified",
                "treatment_dx": "R26.81 - Unsteadiness; R27.8 - Lack of coordination; M62.81 - Muscle weakness",
                "outcomes": {"Berg": (38, 8)},
                "precautions": "prec: fall risk; orthotic use per caregiver; rest breaks PRN.",
                "contra": "contra: seizure activity uncontrolled -> modify/medical clearance.",
                "cpt_plan": ["97112", "97530", "97535"],
            },
        ]

    def vestibular_templates() -> List[Dict[str, Any]]:
        return [
            {
                "title": "BPPV (posterior canal) - right",
                "medical_dx": "H81.11 - Benign paroxysmal vertigo, right ear",
                "treatment_dx": "R42 - Dizziness and giddiness; R26.81 - Unsteadiness on feet",
                "outcomes": {"DHI": (46, 20)},
                "precautions": "prec: fall risk; educate on post-maneuver precautions as tol.",
                "contra": "contra: cervical instability or vertebral artery insufficiency concerns.",
                "cpt_plan": ["95992", "97112", "97535"],
            },
            {
                "title": "Vestibular hypofunction",
                "medical_dx": "H81.90 - Disorder of vestibular function, unspecified ear",
                "treatment_dx": "R42 - Dizziness; R26.81 - Unsteadiness; M62.81 - Muscle weakness",
                "outcomes": {"DHI": (54, 18), "TUG": (12.9, -1.5)},
                "precautions": "prec: fall risk; symptoms may temporarily increase with habituation.",
                "contra": "contra: acute neuro red flags -> ED.",
                "cpt_plan": ["97112", "97530", "97535"],
            },
        ]

    def pelvic_templates() -> List[Dict[str, Any]]:
        return [
            {
                "title": "Stress urinary incontinence",
                "medical_dx": "N39.3 - Stress incontinence (female)",
                "treatment_dx": "M62.89 - Other specified disorders of muscle; R39.15 - Urgency of urination",
                "outcomes": {"PFDI20": (92, 25)},
                "precautions": "prec: obtain consent for pelvic floor exam; trauma-informed approach.",
                "contra": "contra: no consent; acute infection; pelvic pain requiring MD eval.",
                "cpt_plan": ["97110", "97112", "97535"],
            },
            {
                "title": "Pelvic organ prolapse symptoms",
                "medical_dx": "N81.10 - Cystocele, unspecified",
                "treatment_dx": "M62.89 - Other disorders of muscle; R39.15 - Urgency of urination",
                "outcomes": {"PFDI20": (104, 28)},
                "precautions": "prec: consent and privacy; avoid Valsalva during early training.",
                "contra": "contra: unexplained vaginal bleeding -> refer.",
                "cpt_plan": ["97110", "97112", "97535"],
            },
        ]

    TEMPLATE_BY_SERVICE = {
        "Orthopedic": ortho_templates(),
        "Sports": sports_templates(),
        "Neurological": neuro_templates(),
        "Geriatric": geriatric_templates(),
        "Pediatrics": pediatrics_templates(),
        "Vestibular": vestibular_templates(),
        "Pelvic Health": pelvic_templates(),
    }

    SERVICE_DISTRIBUTION: List[Tuple[str, int]] = [
        ("Orthopedic", 30),
        ("Sports", 15),
        ("Neurological", 15),
        ("Geriatric", 15),
        ("Pediatrics", 10),
        ("Vestibular", 10),
        ("Pelvic Health", 5),
    ]

    def make_mrn(i: int) -> str:
        return f"MRN{100000 + i:06d}"

    def make_account(i: int) -> str:
        return f"ACCT{200000 + i:06d}"

    def pick_insurance(i: int) -> Tuple[str, str, str, str, str]:
        payer, plan, typ = random.choice(insurance_plans)
        member = f"{payer[:2].upper()}{random.randint(1000000, 9999999)}"
        group = f"G{random.randint(10000, 99999)}"
        return typ, payer, plan, member, group

    def random_dob(service_line: str) -> date:
        today = date.today()
        if service_line == "Pediatrics":
            years = random.randint(5, 15)
        elif service_line in {"Geriatric"}:
            years = random.randint(67, 89)
        else:
            years = random.randint(18, 66)
        # Randomize month/day
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        return date(today.year - years, month, day)

    def build_goal_list(template: Dict[str, Any], service: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        today = datetime.utcnow().date()
        stg_due = (today + timedelta(days=random.randint(21, 35))).isoformat()
        ltg_due = (today + timedelta(days=random.randint(42, 84))).isoformat()

        # Goal sets vary by service line
        if service in {"Orthopedic", "Sports"}:
            stg = [
                {"text": "Decrease pain by ≥2/10 and improve tol for ADL and work/sport tasks.", "target_date": stg_due, "status": "Continue"},
                {"text": "Improve ROM to within functional limits for targeted joint.", "target_date": stg_due, "status": "Continue"},
            ]
            ltg = [
                {"text": "Return to community amb and stairs w/ no sig gait deviations and pain ≤2/10.", "target_date": ltg_due, "status": "Continue"},
                {"text": "Indep with HEP and self-management; no flare-ups >24 hrs post activity.", "target_date": ltg_due, "status": "Continue"},
            ]
        elif service in {"Neurological", "Geriatric", "Vestibular"}:
            stg = [
                {"text": "Improve balance safety: increase Berg by ≥5 points OR improve TUG by ≥2 sec.", "target_date": stg_due, "status": "Continue"},
                {"text": "Demonstrate safe AD training and fall-prevention strategies w/ caregiver PRN.", "target_date": stg_due, "status": "Continue"},
            ]
            ltg = [
                {"text": "Decrease fall risk and improve functional mobility for community tasks.", "target_date": ltg_due, "status": "Continue"},
                {"text": "Indep with HEP for strength/balance/vestibular program; maintain gains.", "target_date": ltg_due, "status": "Continue"},
            ]
        elif service == "Pediatrics":
            stg = [
                {"text": "Improve gross motor skills: ascend/descend stairs with handrail and minimal assist.", "target_date": stg_due, "status": "Continue"},
                {"text": "Caregiver demonstrates HEP/play activities and safe handling techniques.", "target_date": stg_due, "status": "Continue"},
            ]
            ltg = [
                {"text": "Improve functional mobility and coordination for school/play participation.", "target_date": ltg_due, "status": "Continue"},
                {"text": "Caregiver indep with long-term home program and progressions.", "target_date": ltg_due, "status": "Continue"},
            ]
        else:  # Pelvic Health
            stg = [
                {"text": "Decrease leakage episodes by ≥50% with cough/sneeze/lifting using training strategies.", "target_date": stg_due, "status": "Continue"},
                {"text": "Demonstrate correct pelvic floor contraction and breath coordination (no Valsalva).", "target_date": stg_due, "status": "Continue"},
            ]
            ltg = [
                {"text": "Return to exercise and ADL with minimal to no incontinence and improved QoL score.", "target_date": ltg_due, "status": "Continue"},
                {"text": "Indep with pelvic floor HEP and self-management strategies.", "target_date": ltg_due, "status": "Continue"},
            ]
        return stg, ltg

    def gen_vitals(service: str) -> Dict[str, Any]:
        # Slightly different ranges for peds/geri but keep plausible
        if service == "Pediatrics":
            hr = random.randint(75, 105)
            bp = f"{random.randint(95, 112)}/{random.randint(55, 72)}"
            spo2 = random.randint(97, 100)
        elif service == "Geriatric":
            hr = random.randint(60, 92)
            bp = f"{random.randint(110, 150)}/{random.randint(60, 88)}"
            spo2 = random.randint(94, 99)
        else:
            hr = random.randint(60, 96)
            bp = f"{random.randint(108, 142)}/{random.randint(64, 86)}"
            spo2 = random.randint(95, 100)
        return {"bp": bp, "hr": hr, "spo2": spo2}

    def format_rom(service: str, title: str) -> str:
        # Simple ROM string; varies by service line
        if "knee" in title.lower() or "tka" in title.lower() or "acl" in title.lower():
            flex = random.randint(90, 120)
            ext = random.randint(-8, 0)
            return f"ROM: knee flex {flex}°, ext {ext}°; mild end-range pain."
        if "shoulder" in title.lower() or "rotator" in title.lower():
            flex = random.randint(120, 165)
            abd = random.randint(110, 160)
            er = random.randint(35, 75)
            return f"ROM: shdr flex {flex}°, abd {abd}°, ER {er}°; painful arc noted."
        if "cervical" in title.lower():
            return "ROM: C-spine rot limited with reproduction of sx; postural deficits present."
        if service in {"Neurological", "Geriatric"}:
            return "ROM: gross WNL; mild stiffness noted in hips/ankles with gait."
        if service == "Pelvic Health":
            return "ROM: hip mobility screened; limitations noted in hip IR/ER affecting mechanics."
        return "ROM: gross WNL with mild limitation per assessment."

    def format_mmt(service: str, title: str) -> str:
        if service in {"Orthopedic", "Sports"}:
            return f"Strength: key musculature 3+/5 to 4+/5 with pain inhibition; VC needed for control."
        if service in {"Neurological", "Geriatric"}:
            return "Strength: LE 3/5 to 4-/5; impaired motor control/endurance; requires skilled cueing."
        if service == "Pediatrics":
            return "Strength: age-appropriate screening suggests core/hip weakness; fatigues with play tasks."
        if service == "Vestibular":
            return "Strength: gross 4/5; primary limitation is balance/vestibular integration."
        if service == "Pelvic Health":
            return "Strength: pelvic floor assessed with consent; coordination deficits; core weakness noted."
        return "Strength: deficits noted per exam."

    def gen_subjective(service: str, template: Dict[str, Any], pain: int) -> str:
        # Use approved abbreviations where reasonable (pt, c/o, s/p, ROM, POC, prec, PRN, etc.)
        onset_days = random.choice([7, 14, 21, 30, 45, 60])
        return (
            f"Pt c/o {template['title']} affecting daily function. Onset ~{onset_days} d ago. "
            f"Pain {pain}/10 at worst, {max(0, pain-3)}/10 at best. "
            f"Reports difficulty with ADL, work/school, and community mobility. "
            f"States goal: return to prior activity level and improve function. "
            f"Meds reviewed; allergies reviewed; prec discussed."
        )

    def gen_objective(service: str, template: Dict[str, Any], vitals: Dict[str, Any]) -> str:
        rom = format_rom(service, template["title"])
        mmt = format_mmt(service, template["title"])
        vs = f"VS: BP {vitals['bp']}, HR {vitals['hr']}, SpO2 {vitals['spo2']}%."
        balance = ""
        if service in {"Neurological", "Geriatric"}:
            balance = " Balance: Berg and TUG performed; fall risk education initiated."
        if service == "Vestibular":
            balance = " Vestibular: positional testing performed as tol; VOR exercises initiated."
        if service == "Pediatrics":
            balance = " Motor: age-appropriate balance/coordination tasks assessed via play observation."
        return f"{vs} {rom} {mmt}.{balance}"

    def gen_assessment(service: str, template: Dict[str, Any]) -> str:
        return (
            "Assessment: Findings indicate impairments in pain, mobility, strength, and functional tol "
            "limiting participation. Skilled PT indicated for progression, safety, and patient education. "
            "Prognosis: good with adherence to POC and HEP; barriers addressed as needed."
        )

    def gen_plan(service: str, template: Dict[str, Any]) -> str:
        freq = random.choice(["2x/wk x 6 wks", "2x/wk x 8 wks", "1-2x/wk x 8 wks"])
        return (
            f"Plan: establish POC {freq}. Interventions: TherEx, NMR, TA, pt ed, HEP; progress as tol. "
            "Skilled need: requires clinical decision-making for safe progression, cueing, and monitoring response."
        )

    # -------------------------
    # Create Patients
    # -------------------------
    patients: List[Patient] = []
    patient_index = 0
    for service, count in SERVICE_DISTRIBUTION:
        for _ in range(count):
            fn = first_names[patient_index]
            ln = last_names[patient_index]
            patient_index += 1

            dob = random_dob(service)
            sex = random.choice(["F", "M"])
            mrn = make_mrn(patient_index)
            acct = make_account(patient_index)

            ins_type, payer, plan, member, group = pick_insurance(patient_index)
            phys, phys_phone = random.choice(referring_physicians)

            template = random.choice(TEMPLATE_BY_SERVICE[service])

            patient = Patient(
                mrn=mrn,
                account_number=acct,
                first_name=fn,
                last_name=ln,
                dob=dob,
                sex=sex,
                phone=f"555-{random.randint(1000, 9999)}",
                email=f"{fn.lower()}.{ln.lower()}@example.test",
                address=f"{random.randint(100, 999)} {random.choice(['Maple','Oak','Pine','Cedar','Lake','Hill'])} St",
                emergency_contact_name=f"{random.choice(first_names)} {random.choice(last_names)}",
                emergency_contact_phone=f"555-{random.randint(1000, 9999)}",
                insurance_type=ins_type,
                insurance_payer=payer,
                insurance_plan=plan,
                insurance_member_id=member,
                insurance_group=group,
                referring_physician=phys,
                referring_physician_phone=phys_phone,
                service_line=service,
                primary_dx=template.get("medical_dx"),
                secondary_dx=None,
                treatment_dx=template.get("treatment_dx"),
                precautions=template.get("precautions"),
                contraindications=template.get("contra"),
                case_summary=f"Service line: {service}. Working dx: {template['title']}. Synthetic teaching case.",
            )
            db.session.add(patient)
            patients.append(patient)

    db.session.flush()

    # Add allergies and meds (synthetic)
    common_allergies = [
        ("NKA", None, None),
        ("Penicillin", "rash", "Moderate"),
        ("NSAIDs", "GI upset", "Mild"),
        ("Latex", "itching", "Mild"),
        ("Sulfa", "hives", "Moderate"),
    ]
    common_meds = [
        ("Acetaminophen", "500 mg", "PO", "q6h PRN"),
        ("Ibuprofen", "400 mg", "PO", "q6-8h PRN"),
        ("Lisinopril", "10 mg", "PO", "qd"),
        ("Metformin", "500 mg", "PO", "bid"),
        ("Atorvastatin", "20 mg", "PO", "qd"),
    ]

    for p in patients:
        # 70% NKA
        if random.random() < 0.7:
            db.session.add(Allergy(patient_id=p.id, substance="NKA", reaction=None, severity=None))
        else:
            sub, rxn, sev = random.choice(common_allergies[1:])
            db.session.add(Allergy(patient_id=p.id, substance=sub, reaction=rxn, severity=sev))

        # 1-3 meds depending on age/service
        med_count = 1 if p.service_line == "Pediatrics" else random.randint(1, 3)
        for _ in range(med_count):
            name, dose, route, freq = random.choice(common_meds)
            db.session.add(Medication(patient_id=p.id, name=name, dose=dose, route=route, frequency=freq, status="Active"))

        # Problems list example
        if p.service_line in {"Geriatric", "Neurological"}:
            db.session.add(Problem(patient_id=p.id, description="Fall risk", status="Active"))
        if p.service_line == "Pelvic Health":
            db.session.add(Problem(patient_id=p.id, description="Pelvic floor coordination deficit", status="Active"))

    db.session.flush()

    # -------------------------
    # Encounters
    # -------------------------
    def add_encounter(
        patient: Patient,
        when: datetime,
        provider: User,
        encounter_type: str,
        template: str,
        subject: str,
        obj: str,
        assess: str,
        plan_text: str,
        pain_pre: Optional[int],
        pain_post: Optional[int],
        vitals: Dict[str, Any],
        outcomes: Dict[str, Any],
        extra: Dict[str, Any],
        charges: List[Tuple[str, int, Optional[int], Optional[str]]],
        locked_signed: bool = True,
    ) -> Encounter:
        enc = Encounter(
            patient_id=patient.id,
            provider_id=provider.id,
            encounter_date=when,
            encounter_type=encounter_type,
            location="Outpatient PT",
            status="Signed" if locked_signed else "Draft",
            signed_at=when if locked_signed else None,
            locked=locked_signed,
        )
        db.session.add(enc)
        db.session.flush()

        note = Note(
            encounter_id=enc.id,
            template=template,
            subjective=subject,
            objective=obj,
            assessment=assess,
            plan=plan_text,
            pain_pre=pain_pre,
            pain_post=pain_post,
            vitals_json=vitals,
            outcome_json=outcomes,
            extra_json=extra,
        )
        db.session.add(note)
        db.session.flush()

        for code, units, minutes, mod in charges:
            db.session.add(
                Charge(
                    encounter_id=enc.id,
                    cpt_code=code,
                    description=None,
                    minutes=minutes,
                    units=units,
                    modifiers=mod,
                )
            )
        return enc

    today = datetime.utcnow()

    # Choose which patients are "established" with progress reports
    established_ids = set(random.sample([p.id for p in patients], 45))
    discharged_ids = set(random.sample(list(established_ids), 20))

    for p in patients:
        service = p.service_line or "Orthopedic"
        template = random.choice(TEMPLATE_BY_SERVICE[service])

        # Date logic: new pts eval within last 14 days; established eval 45-90 days ago
        if p.id in established_ids:
            eval_dt = today - timedelta(days=random.randint(45, 95))
        else:
            eval_dt = today - timedelta(days=random.randint(3, 14))

        vitals = gen_vitals(service)
        pain = random.randint(0, 7) if service in {"Neurological", "Geriatric", "Vestibular"} else random.randint(2, 8)

        subj = gen_subjective(service, template, pain)
        obj = gen_objective(service, template, vitals)
        assess = gen_assessment(service, template)
        pl = gen_plan(service, template)

        stg, ltg = build_goal_list(template, service)

        # Outcomes baseline
        outcomes: Dict[str, Any] = {}
        if template.get("outcomes"):
            for k, v in template["outcomes"].items():
                if v is None:
                    continue
                base_val, _delta = v
                outcomes[k] = base_val

        extra_eval: Dict[str, Any] = {
            "evaluation_date": eval_dt.date().isoformat(),
            "recertification_date": (eval_dt.date() + timedelta(days=90)).isoformat(),
            "referral_mechanism": "Physician referral",
            "medical_dx": p.primary_dx or template.get("medical_dx"),
            "treatment_dx": p.treatment_dx or template.get("treatment_dx"),
            "referring_physician": p.referring_physician,
            "evaluation_therapist": instructor.signature_line,
            "frequency_duration": random.choice(["2x/wk x 6 wks", "2x/wk x 8 wks", "1-2x/wk x 8 wks"]),
            "pta_may_treat": True,
            "history": "Hx: denies recent falls unless noted; PMH reviewed; meds reviewed; allergies reviewed; learning style assessed.",
            "systems_review": "Systems review: CV/pulm screened; integumentary screened; MSK/neuro screened; cognition/communication appropriate for participation.",
            "tests_measures_rom": format_rom(service, template["title"]),
            "tests_measures_mmt": format_mmt(service, template["title"]),
            "functional_limitations": "Limits in ADL, IADL, work/sport/recreation and community mobility per report.",
            "problem_list": "Problem list: pain, ↓ strength, ↓ ROM/mobility, ↓ balance/endurance as applicable; limits participation.",
            "prognosis": "Prognosis: good rehab pot with adherence; anticipate progress toward goals with skilled services.",
            "plan_of_care": "Interventions: TherEx, NMR, TA, manual PRN, gait/balance, pt ed, HEP, modalities PRN.",
            "discharge_plan": "Anticipated d/c to indep HEP with functional goals met; follow up with phys PRN.",
            "contraindications": p.contraindications or template.get("contra"),
            "precautions": p.precautions or template.get("precautions"),
            "contraindications_reviewed": True,
            "patient_consent": True,
            "informed_consent": True,
            "required_cpt": template.get("cpt_plan", []),
            "stg": stg,
            "ltg": ltg,
            "therapist_signature": instructor.signature_line,
            "therapist_signature_date": eval_dt.date().isoformat(),
            "physician_signature": p.referring_physician or "",
            "physician_signature_date": "",
            "poc_sent_to_physician": True,
        }

        # Evaluation charge code complexity selection
        eval_code = random.choice(["97161", "97162", "97163"])
        add_encounter(
            patient=p,
            when=eval_dt,
            provider=instructor,
            encounter_type="Evaluation",
            template="Evaluation",
            subject=subj,
            obj=obj,
            assess=assess,
            plan_text=pl,
            pain_pre=pain,
            pain_post=max(0, pain - random.randint(0, 2)),
            vitals=vitals,
            outcomes=outcomes,
            extra=extra_eval,
            charges=[(eval_code, 1, None, None)],
            locked_signed=True,
        )

        # Some patients get 1-4 visit notes even if new
        visit_count = random.randint(0, 2) if p.id not in established_ids else random.randint(4, 10)
        last_visit_dt = eval_dt

        for v in range(visit_count):
            last_visit_dt = last_visit_dt + timedelta(days=random.randint(2, 7))
            provider = random.choice([student1, student2, instructor])

            visit_vitals = gen_vitals(service)
            pre = max(0, pain - random.randint(0, 2))
            post = max(0, pre - random.randint(0, 2))

            subj_v = (
                f"Pt reports {random.choice(['mild','mod','sig'])} improvement in function; "
                f"pain {pre}/10 pre, reports HEP compliance {random.choice(['good','fair','inconsistent'])}. "
                f"Denies new red flags. Prec reviewed."
            )
            obj_v = (
                f"Interventions provided per POC with skilled cueing: TherEx/NMR/TA as appropriate; "
                f"progressed parameters as tol. VS: BP {visit_vitals['bp']}, HR {visit_vitals['hr']}, SpO2 {visit_vitals['spo2']}%."
            )
            assess_v = (
                "Response: tolerated session without adverse rxn. "
                "Skilled need: VC/TC for form, safety, and progression; monitoring response and modifying intensity."
            )
            plan_v = (
                "Plan next visit: progress functional tasks, update HEP, reinforce precautions; continue POC. "
                "Communication/consultation documented as needed."
            )

            extra_daily = {
                "visit_status": "Completed",
                "cancellations_no_shows": "0",
                "changes_in_status": "Small gains in mobility/strength or balance per session; monitor symptom response.",
                "adverse_reactions": "None",
                "factors_modifying": "Adherence, pain, fatigue, and safety considerations affect progression parameters.",
                "communication": "Reviewed HEP, precautions, and plan with pt; caregiver involved PRN.",
                "continuation_modifications": "Continue POC; modify intensity/volume based on response.",
                "therapist_signature": provider.signature_line,
                "therapist_signature_date": last_visit_dt.date().isoformat(),
            }

            # Example charges for a visit (minutes + units)
            # Keep totals realistic (30-60 min)
            visit_codes = template.get("cpt_plan", ["97110", "97112"])
            chosen = random.sample(visit_codes, k=min(len(visit_codes), random.randint(2, 3)))
            charges = []
            total = 0
            for code in chosen:
                mins = random.choice([10, 12, 15, 20])
                total += mins
                units = 1 if mins < 23 else 2
                charges.append((code, units, mins, None))
            # Add untimed modality occasionally
            if random.random() < 0.15:
                charges.append(("97010", 1, None, None))

            add_encounter(
                patient=p,
                when=last_visit_dt,
                provider=provider,
                encounter_type="Daily Visit Note",
                template="Daily",
                subject=subj_v,
                obj=obj_v,
                assess=assess_v,
                plan_text=plan_v,
                pain_pre=pre,
                pain_post=post,
                vitals=visit_vitals,
                outcomes={},
                extra=extra_daily,
                charges=charges,
                locked_signed=True,
            )

        # Progress reports for established patients
        if p.id in established_ids:
            prog_dt = last_visit_dt + timedelta(days=random.randint(5, 14))

            # Update outcomes vs baseline if present
            prog_outcomes = dict(outcomes)
            for k, v in template.get("outcomes", {}).items():
                if v is None:
                    continue
                base_val, delta = v
                if k in {"TUG"}:
                    prog_outcomes[k] = max(5.0, float(base_val) + float(delta))  # delta negative improves
                else:
                    prog_outcomes[k] = max(0, float(base_val) - float(delta)) if k in {"Oswestry","NDI","DHI","PFDI20"} else float(base_val) + float(delta)

            # Goal status: mark 0-1 STG as completed
            stg_prog = [dict(g) for g in stg]
            if stg_prog and random.random() < 0.7:
                stg_prog[0]["status"] = "Completed"
            ltg_prog = [dict(g) for g in ltg]

            subj_p = (
                "Progress Report: Pt reports improved function since eval; pain decreased and tol improved. "
                "Attendance: minimal cancellations/no-shows unless noted. HEP compliance improved."
            )
            obj_p = (
                f"Objective update: {format_rom(service, template['title'])} "
                f"Strength and functional tasks improved with skilled cueing. "
                f"Updated measures recorded (e.g., Berg/TUG/LEFS/Oswestry/NDI/DHI/PFDI-20 as applicable). "
                f"VS: BP {vitals['bp']}, HR {vitals['hr']}, SpO2 {vitals['spo2']}%."
            )
            assess_p = (
                "Assessment: documents extent of progress vs baseline; pt continues to require skilled PT for safe progression, "
                "clinical decision-making, and goal attainment. Factors affecting progression addressed (adherence, pain, fatigue). "
                "POC modifications documented as indicated."
            )
            plan_p = (
                "Plan: continue skilled PT per updated POC; progress interventions with clear parameters; reinforce precautions and HEP."
            )

            extra_prog: Dict[str, Any] = {
                "progress_date": prog_dt.date().isoformat(),
                "recertification_date": (eval_dt.date() + timedelta(days=90)).isoformat(),
                "evaluation_date": eval_dt.date().isoformat(),
                "medical_dx": p.primary_dx,
                "treatment_dx": p.treatment_dx,
                "cancellations_no_shows": str(random.randint(0, 2)),
                "clinical_assessment_functional_progress": "Pt demonstrates measurable improvement in function; see updated objective measures and goal status.",
                "communication": "Consult/communication with pt/caregiver and referring phys as needed; updated POC discussed.",
                "plan_modifications": "Modify goals/interventions as appropriate based on progress and response.",
                "continued_need": "Continued skilled services required for safety, progression, and to reach functional goals.",
                "frequency_duration": random.choice(["2x/wk x 4 wks", "1-2x/wk x 6 wks"]),
                "required_cpt": template.get("cpt_plan", []),
                "stg": stg_prog,
                "ltg": ltg_prog,
                "therapist_signature": instructor.signature_line,
                "therapist_signature_date": prog_dt.date().isoformat(),
                "physician_signature": p.referring_physician or "",
                "physician_signature_date": "",
                "poc_sent_to_physician": True,
            }

            add_encounter(
                patient=p,
                when=prog_dt,
                provider=instructor,
                encounter_type="Progress Report",
                template="Progress",
                subject=subj_p,
                obj=obj_p,
                assess=assess_p,
                plan_text=plan_p,
                pain_pre=max(0, pain - 2),
                pain_post=max(0, pain - 3),
                vitals=gen_vitals(service),
                outcomes=prog_outcomes,
                extra=extra_prog,
                charges=[],
                locked_signed=True,
            )

            # Optional discharge summary
            if p.id in discharged_ids:
                dc_dt = prog_dt + timedelta(days=random.randint(7, 21))
                subj_d = "Discharge Summary: Pt reports readiness for discharge and indep self-management."
                obj_d = "Objective: functional status improved; goals/outcomes reviewed; HEP reviewed."
                assess_d = "Assessment: criteria for termination met (goals met/plateau/indep HEP as applicable). "
                plan_d = "Plan: discharge to HEP; f/u with referring phys PRN; return precautions reviewed."

                extra_dc = {
                    "discharge_date": dc_dt.date().isoformat(),
                    "criteria_termination": random.choice(["Goals met", "Functional plateau", "Independent with HEP"]),
                    "current_status": "Current physical/functional status documented with objective measures as appropriate.",
                    "goals_outcomes": "Degree of goals achieved documented; reasons for unmet goals documented if applicable.",
                    "continuing_care": "HEP provided; education for self-management; communication with phys PRN.",
                    "therapist_signature": instructor.signature_line,
                    "therapist_signature_date": dc_dt.date().isoformat(),
                    "physician_signature": p.referring_physician or "",
                    "physician_signature_date": "",
                }

                add_encounter(
                    patient=p,
                    when=dc_dt,
                    provider=instructor,
                    encounter_type="Discharge Summary",
                    template="Discharge",
                    subject=subj_d,
                    obj=obj_d,
                    assess=assess_d,
                    plan_text=plan_d,
                    pain_pre=max(0, pain - 3),
                    pain_post=max(0, pain - 4),
                    vitals=gen_vitals(service),
                    outcomes=prog_outcomes,
                    extra=extra_dc,
                    charges=[],
                    locked_signed=True,
                )

    # -------------------------
    # Appointments (optional realism)
    # -------------------------
    # Add a handful of upcoming appointments for dashboard view
    future_patients = random.sample(patients, 12)
    for i, p in enumerate(future_patients):
        start = datetime.utcnow() + timedelta(days=random.randint(1, 7), hours=random.randint(8, 15))
        end = start + timedelta(minutes=45)
        provider = random.choice(providers)
        db.session.add(
            Appointment(
                patient_id=p.id,
                provider_id=provider.id,
                start_at=start,
                end_at=end,
                location="Outpatient PT",
                status="Scheduled",
            )
        )

    db.session.commit()
