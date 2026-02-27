from __future__ import annotations

from datetime import datetime, timedelta, date
from functools import wraps
from typing import Dict, Any, List, Optional

from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from extensions import db, login_manager
from models import User, Patient, Encounter, Note, Charge, Appointment, AuditLog
from seed import ensure_seed_data


# -------------------------
# CPT catalog (educational)
# -------------------------
# timed=True indicates time-based codes where minutes are typically tracked.
CPT_CATALOG = [
    {"code": "97161", "desc": "PT Evaluation - low complexity", "timed": False},
    {"code": "97162", "desc": "PT Evaluation - moderate complexity", "timed": False},
    {"code": "97163", "desc": "PT Evaluation - high complexity", "timed": False},
    {"code": "97164", "desc": "PT Re-evaluation", "timed": False},

    {"code": "97110", "desc": "Therapeutic exercise", "timed": True},
    {"code": "97112", "desc": "Neuromuscular re-education", "timed": True},
    {"code": "97116", "desc": "Gait training", "timed": True},
    {"code": "97140", "desc": "Manual therapy", "timed": True},
    {"code": "97530", "desc": "Therapeutic activities", "timed": True},
    {"code": "97535", "desc": "Self-care/home management training", "timed": True},
    {"code": "97113", "desc": "Aquatic therapy/exercises", "timed": True},
    {"code": "97760", "desc": "Orthotic management/training", "timed": True},
    {"code": "97761", "desc": "Prosthetic training", "timed": True},

    {"code": "95992", "desc": "Canalith repositioning procedure (e.g., BPPV)", "timed": False},

    {"code": "97010", "desc": "Hot/cold packs", "timed": False},
    {"code": "97012", "desc": "Mechanical traction", "timed": False},
    {"code": "97014", "desc": "Electrical stimulation (unattended)", "timed": False},
    {"code": "97035", "desc": "Ultrasound", "timed": True},
]

CPT_INDEX = {c["code"]: c for c in CPT_CATALOG}


def compute_units_from_minutes(minutes: Optional[int]) -> int:
    """Simple educational estimator: 8-minute rule approximation per code.
    NOTE: Real-world billing can require aggregation across timed codes; this is a teaching aid only.
    """
    if minutes is None:
        return 0
    if minutes < 8:
        return 0
    # 8-22 = 1 unit, 23-37 = 2, 38-52 = 3, 53-67 = 4, etc.
    return int((minutes + 7) // 15)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()
        ensure_seed_data()

    # -------------------------
    # Auth helpers
    # -------------------------
    @login_manager.user_loader
    def load_user(user_id: str) -> Optional[User]:
        return User.query.get(int(user_id))

    def log_action(action: str, patient_id: int | None = None, encounter_id: int | None = None, details: str | None = None):
        try:
            if current_user.is_authenticated:
                db.session.add(
                    AuditLog(
                        user_id=current_user.id,
                        patient_id=patient_id,
                        encounter_id=encounter_id,
                        action=action,
                        details=details,
                    )
                )
                db.session.commit()
        except Exception:
            db.session.rollback()

    def instructor_required(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if not current_user.is_instructor():
                abort(403)
            return view_func(*args, **kwargs)
        return wrapper

    @app.context_processor
    def inject_globals():
        return {
            "app_name": "PTA EMR Playground",
            "now": datetime.utcnow(),
            "CPT_CATALOG": CPT_CATALOG,
            "CPT_INDEX": CPT_INDEX,
            "compute_units_from_minutes": compute_units_from_minutes,
        }

    # -------------------------
    # Routes
    # -------------------------
    @app.route("/health")
    def health():
        return {"status": "ok"}

    # ---- Auth ----
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""
            remember = bool(request.form.get("remember"))

            user = User.query.filter_by(email=email).first()
            if not user or not check_password_hash(user.password_hash, password):
                flash("Invalid email or password.", "danger")
                return render_template("auth/login.html")

            login_user(user, remember=remember)
            log_action("login", details=f"email={email}")
            flash(f"Welcome, {user.name}.", "success")
            return redirect(url_for("dashboard"))

        return render_template("auth/login.html")

    @app.route("/logout")
    @login_required
    def logout():
        log_action("logout")
        logout_user()
        flash("Signed out.", "info")
        return redirect(url_for("login"))

    # ---- Dashboard ----
    @app.route("/")
    @login_required
    def dashboard():
        q = (request.args.get("q") or "").strip()
        if q:
            like = f"%{q}%"
            patients = Patient.query.filter(
                (Patient.last_name.ilike(like)) |
                (Patient.first_name.ilike(like)) |
                (Patient.mrn.ilike(like)) |
                (Patient.account_number.ilike(like))
            ).order_by(Patient.last_name.asc()).limit(50).all()
        else:
            patients = Patient.query.order_by(Patient.last_name.asc()).limit(15).all()

        # Recent encounters
        recent_encounters = Encounter.query.order_by(Encounter.encounter_date.desc()).limit(10).all()

        # Upcoming appointments (next 7 days)
        start = datetime.utcnow()
        end = start + timedelta(days=7)
        appts = Appointment.query.filter(
            Appointment.start_at >= start,
            Appointment.start_at <= end
        ).order_by(Appointment.start_at.asc()).limit(25).all()

        return render_template("dashboard.html", patients=patients, q=q, recent_encounters=recent_encounters, appts=appts)

    # ---- Resources ----
    @app.route("/resources")
    @login_required
    def resources():
        return render_template("resources.html")

    # ---- Patients ----
    @app.route("/patients")
    @login_required
    def patients_list():
        q = (request.args.get("q") or "").strip()
        service = (request.args.get("service") or "").strip()

        query = Patient.query
        if q:
            like = f"%{q}%"
            query = query.filter(
                (Patient.last_name.ilike(like)) |
                (Patient.first_name.ilike(like)) |
                (Patient.mrn.ilike(like)) |
                (Patient.account_number.ilike(like))
            )
        if service:
            query = query.filter(Patient.service_line == service)

        patients = query.order_by(Patient.last_name.asc()).all()
        services = [r[0] for r in db.session.query(Patient.service_line).distinct().order_by(Patient.service_line.asc()).all() if r[0]]
        return render_template("patients/list.html", patients=patients, q=q, service=service, services=services)

    @app.route("/patients/<int:patient_id>")
    @login_required
    def patient_detail(patient_id: int):
        patient = Patient.query.get_or_404(patient_id)
        encounters = Encounter.query.filter_by(patient_id=patient_id).order_by(Encounter.encounter_date.desc()).all()

        # Find latest evaluation for quick access
        latest_eval = (
            Encounter.query.filter_by(patient_id=patient_id, encounter_type="Evaluation")
            .order_by(Encounter.encounter_date.desc())
            .first()
        )

        return render_template("patients/detail.html", patient=patient, encounters=encounters, latest_eval=latest_eval)

    # ---- Encounters ----
    NOTE_TYPES = [
        ("Evaluation", "Evaluation"),
        ("Daily Visit Note", "Daily"),
        ("Progress Report", "Progress"),
        ("Discharge Summary", "Discharge"),
    ]

    def _default_note_for(template: str, patient: Patient, provider: User) -> Dict[str, Any]:
        """Provide a reasonable default structure for a new note."""
        extra: Dict[str, Any] = {}

        # Defaults that are helpful for Medicare-style documentation and course structure
        extra["evaluation_date"] = datetime.utcnow().date().isoformat()
        extra["recertification_date"] = (datetime.utcnow().date() + timedelta(days=90)).isoformat()
        extra["referral_mechanism"] = "Physician referral"
        extra["contraindications"] = patient.contraindications or ""
        extra["precautions"] = patient.precautions or ""
        extra["patient_consent"] = True
        extra["informed_consent"] = True
        extra["therapist_signature"] = provider.signature_line
        extra["therapist_signature_date"] = datetime.utcnow().date().isoformat()
        extra["physician_signature"] = ""
        extra["physician_signature_date"] = ""
        extra["frequency_duration"] = "2x/wk x 6 wks"
        extra["pta_may_treat"] = True

        # Goals - initialize empty rows
        extra["stg"] = [{"text": "", "target_date": "", "status": "Continue"}]
        extra["ltg"] = [{"text": "", "target_date": "", "status": "Continue"}]

        # Try to pull from latest evaluation/progress where appropriate
        if template in {"Daily", "Progress", "Discharge"}:
            latest = (
                Encounter.query.join(Note, Encounter.id == Note.encounter_id)
                .filter(Encounter.patient_id == patient.id, Note.template.in_(["Evaluation", "Progress"]))
                .order_by(Encounter.encounter_date.desc())
                .first()
            )
            if latest and latest.note:
                src = latest.note.extra_json or {}
                for k in ["frequency_duration", "recertification_date", "referral_mechanism"]:
                    if src.get(k):
                        extra[k] = src.get(k)
                # Copy goals forward
                if src.get("stg"):
                    extra["stg"] = src.get("stg")
                if src.get("ltg"):
                    extra["ltg"] = src.get("ltg")
                # Carry diagnosis forward (but editable)
                for k in ["medical_dx", "treatment_dx"]:
                    if src.get(k):
                        extra[k] = src.get(k)

        return extra

    @app.route("/patients/<int:patient_id>/encounters/new", methods=["GET", "POST"])
    @login_required
    def encounter_new(patient_id: int):
        patient = Patient.query.get_or_404(patient_id)

        if request.method == "POST":
            encounter_type = request.form.get("encounter_type") or "Daily Visit Note"
            template = dict(NOTE_TYPES).get(encounter_type, "Daily")

            when_str = request.form.get("encounter_date") or ""
            try:
                when = datetime.fromisoformat(when_str) if when_str else datetime.utcnow()
            except ValueError:
                when = datetime.utcnow()

            location = (request.form.get("location") or "Outpatient PT").strip() or "Outpatient PT"

            enc = Encounter(
                patient_id=patient.id,
                provider_id=current_user.id,
                encounter_date=when,
                encounter_type=encounter_type,
                location=location,
                status="Draft",
                locked=False,
            )
            db.session.add(enc)
            db.session.flush()

            note = Note(
                encounter_id=enc.id,
                template=template,
                subjective="",
                objective="",
                assessment="",
                plan="",
                vitals_json={},
                outcome_json={},
                extra_json=_default_note_for(template, patient, current_user),
            )
            db.session.add(note)
            db.session.commit()
            log_action("encounter_create", patient_id=patient.id, encounter_id=enc.id, details=f"type={encounter_type}")

            flash("Encounter created.", "success")
            return redirect(url_for("encounter_edit", encounter_id=enc.id))

        return render_template("encounters/new.html", patient=patient, NOTE_TYPES=NOTE_TYPES)

    def _parse_goals(prefix: str) -> List[Dict[str, str]]:
        texts = request.form.getlist(f"{prefix}_text")
        dates = request.form.getlist(f"{prefix}_date")
        statuses = request.form.getlist(f"{prefix}_status")
        goals: List[Dict[str, str]] = []
        for i in range(max(len(texts), len(dates), len(statuses))):
            text = (texts[i] if i < len(texts) else "").strip()
            dt = (dates[i] if i < len(dates) else "").strip()
            status = (statuses[i] if i < len(statuses) else "Continue").strip() or "Continue"
            if text or dt:
                goals.append({"text": text, "target_date": dt, "status": status})
        # Always keep at least one row for UX
        if not goals:
            goals = [{"text": "", "target_date": "", "status": "Continue"}]
        return goals

    def _update_charges(enc: Encounter):
        # Remove existing charges
        Charge.query.filter_by(encounter_id=enc.id).delete()

        codes = request.form.getlist("charge_code")
        descs = request.form.getlist("charge_desc")
        minutes_list = request.form.getlist("charge_minutes")
        units_list = request.form.getlist("charge_units")
        mods = request.form.getlist("charge_mod")

        for i, code in enumerate(codes):
            code = (code or "").strip()
            if not code:
                continue

            desc = (descs[i] if i < len(descs) else "").strip()
            minutes_raw = (minutes_list[i] if i < len(minutes_list) else "").strip()
            units_raw = (units_list[i] if i < len(units_list) else "").strip()
            mod = (mods[i] if i < len(mods) else "").strip()

            minutes_val: Optional[int] = None
            if minutes_raw:
                try:
                    minutes_val = int(minutes_raw)
                except ValueError:
                    minutes_val = None

            units_val: int = 1
            if units_raw:
                try:
                    units_val = int(units_raw)
                except ValueError:
                    units_val = 1
            else:
                # If units blank but minutes present and code is timed, estimate units
                meta = CPT_INDEX.get(code, {})
                if meta.get("timed") and minutes_val is not None:
                    u = compute_units_from_minutes(minutes_val)
                    units_val = max(1, u) if minutes_val >= 8 else 0

            # Auto-description if not provided
            if not desc and code in CPT_INDEX:
                desc = CPT_INDEX[code]["desc"]

            db.session.add(
                Charge(
                    encounter_id=enc.id,
                    cpt_code=code,
                    description=desc or None,
                    minutes=minutes_val,
                    units=units_val,
                    modifiers=mod or None,
                )
            )

    @app.route("/encounters/<int:encounter_id>")
    @login_required
    def encounter_view(encounter_id: int):
        enc = Encounter.query.get_or_404(encounter_id)
        patient = enc.patient
        note = enc.note

        total_minutes = sum([c.minutes or 0 for c in enc.charges])
        total_units = sum([c.units or 0 for c in enc.charges])

        return render_template(
            "encounters/detail.html",
            enc=enc,
            patient=patient,
            note=note,
            total_minutes=total_minutes,
            total_units=total_units,
        )

    @app.route("/encounters/<int:encounter_id>/edit", methods=["GET", "POST"])
    @login_required
    def encounter_edit(encounter_id: int):
        enc = Encounter.query.get_or_404(encounter_id)
        patient = enc.patient
        note = enc.note

        if enc.locked:
            flash("This encounter is locked. An instructor must unlock it to edit.", "warning")
            return redirect(url_for("encounter_view", encounter_id=enc.id))

        if request.method == "POST":
            # Update narrative sections
            note.subjective = request.form.get("subjective") or ""
            note.objective = request.form.get("objective") or ""
            note.assessment = request.form.get("assessment") or ""
            note.plan = request.form.get("plan") or ""

            # Pain
            def _int_or_none(x):
                x = (x or "").strip()
                if not x:
                    return None
                try:
                    return int(x)
                except ValueError:
                    return None

            note.pain_pre = _int_or_none(request.form.get("pain_pre"))
            note.pain_post = _int_or_none(request.form.get("pain_post"))

            # Vitals
            vitals = dict(note.vitals_json or {})
            vitals["bp"] = (request.form.get("v_bp") or "").strip()
            vitals["hr"] = _int_or_none(request.form.get("v_hr"))
            vitals["spo2"] = _int_or_none(request.form.get("v_spo2"))
            note.vitals_json = vitals

            # Outcomes
            outcomes = dict(note.outcome_json or {})
            for key in ["Berg", "TUG", "LEFS", "Oswestry", "NDI", "DHI", "PFDI20", "PedsQL"]:
                raw = (request.form.get(f"o_{key}") or "").strip()
                if raw == "":
                    outcomes.pop(key, None)
                    continue
                try:
                    outcomes[key] = float(raw) if "." in raw else int(raw)
                except ValueError:
                    outcomes[key] = raw
            note.outcome_json = outcomes

            # Template-specific extras (simple key/value)
            extra = dict(note.extra_json or {})
            for k, v in request.form.items():
                if k.startswith("extra_"):
                    extra[k[len("extra_"):]] = v

            # Checkbox-style extras (absent => False)
            for b in ["patient_consent", "informed_consent", "pta_may_treat", "poc_sent_to_physician", "contraindications_reviewed"]:
                extra[b] = bool(request.form.get(f"extra_{b}"))

            # Goals
            extra["stg"] = _parse_goals("stg")
            extra["ltg"] = _parse_goals("ltg")

            # Required CPT codes planned
            extra["required_cpt"] = request.form.getlist("required_cpt")

            note.extra_json = extra

            # Charges
            _update_charges(enc)

            db.session.commit()
            log_action("encounter_update", patient_id=patient.id, encounter_id=enc.id, details=f"template={note.template}")
            flash("Saved.", "success")
            return redirect(url_for("encounter_view", encounter_id=enc.id))

        return render_template("encounters/edit.html", enc=enc, patient=patient, note=note, NOTE_TYPES=NOTE_TYPES)

    @app.route("/encounters/<int:encounter_id>/sign", methods=["POST"])
    @login_required
    def encounter_sign(encounter_id: int):
        enc = Encounter.query.get_or_404(encounter_id)
        if enc.locked:
            flash("Encounter already locked.", "info")
            return redirect(url_for("encounter_view", encounter_id=enc.id))

        enc.status = "Signed"
        enc.signed_at = datetime.utcnow()
        enc.locked = True
        db.session.commit()
        log_action("encounter_sign", patient_id=enc.patient_id, encounter_id=enc.id)
        flash("Signed and locked.", "success")
        return redirect(url_for("encounter_view", encounter_id=enc.id))

    @app.route("/encounters/<int:encounter_id>/unlock", methods=["POST"])
    @login_required
    def encounter_unlock(encounter_id: int):
        enc = Encounter.query.get_or_404(encounter_id)

        # Allow instructors/admins to unlock any encounter; allow the encounter author to unlock their own note.
        if not (current_user.is_instructor() or current_user.id == enc.provider_id):
            abort(403)

        enc.locked = False
        enc.status = "Draft"
        enc.signed_at = None
        db.session.commit()
        log_action("encounter_unlock", patient_id=enc.patient_id, encounter_id=enc.id)
        flash("Unlocked. Encounter returned to Draft for editing.", "warning")
        return redirect(url_for("encounter_edit", encounter_id=enc.id))

    # ---- Admin ----
    @app.route("/admin")
    @login_required
    @instructor_required
    def admin_home():
        users = User.query.order_by(User.role.asc(), User.name.asc()).all()
        patient_count = Patient.query.count()
        encounter_count = Encounter.query.count()
        return render_template("admin/home.html", users=users, patient_count=patient_count, encounter_count=encounter_count)

    @app.route("/admin/reset", methods=["POST"])
    @login_required
    @instructor_required
    def admin_reset():
        # Drop and recreate for demo usage
        db.drop_all()
        db.create_all()
        ensure_seed_data(force=True)
        flash("Database reset and reseeded.", "success")
        return redirect(url_for("admin_home"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
