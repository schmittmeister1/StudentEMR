from __future__ import annotations

from datetime import date, datetime
from typing import Optional, List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin

from extensions import db

def now_utc() -> datetime:
    return datetime.utcnow()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    email: Mapped[str] = mapped_column(db.String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(db.String(120), nullable=False)
    role: Mapped[str] = mapped_column(db.String(30), default="student", nullable=False)  # student|instructor|admin

    credentials: Mapped[Optional[str]] = mapped_column(db.String(80), nullable=True)     # e.g., "PT, DPT" or "PTA"
    license_number: Mapped[Optional[str]] = mapped_column(db.String(40), nullable=True)

    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)

    encounters: Mapped[List["Encounter"]] = relationship("Encounter", back_populates="provider")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="provider")

    def get_id(self) -> str:
        return str(self.id)

    def is_instructor(self) -> bool:
        return self.role in {"instructor", "admin"}

    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def display_name(self) -> str:
        if self.credentials:
            return f"{self.name}, {self.credentials}"
        return self.name

    @property
    def signature_line(self) -> str:
        parts = [self.display_name]
        if self.license_number:
            parts.append(f"Lic #{self.license_number}")
        return " | ".join(parts)


class Patient(db.Model):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)

    mrn: Mapped[str] = mapped_column(db.String(32), unique=True, index=True, nullable=False)
    account_number: Mapped[str] = mapped_column(db.String(32), unique=True, index=True, nullable=False)

    first_name: Mapped[str] = mapped_column(db.String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(db.String(80), nullable=False)

    dob: Mapped[date] = mapped_column(db.Date, nullable=False)
    sex: Mapped[str] = mapped_column(db.String(20), nullable=False)

    phone: Mapped[Optional[str]] = mapped_column(db.String(40), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    emergency_contact_name: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(db.String(40), nullable=True)

    # Insurance / payer (synthetic)
    insurance_type: Mapped[Optional[str]] = mapped_column(db.String(40), nullable=True)   # Medicare|Commercial|Medicaid|Tricare|Self-pay
    insurance_payer: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    insurance_plan: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    insurance_member_id: Mapped[Optional[str]] = mapped_column(db.String(60), nullable=True)
    insurance_group: Mapped[Optional[str]] = mapped_column(db.String(60), nullable=True)

    referring_physician: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    referring_physician_phone: Mapped[Optional[str]] = mapped_column(db.String(40), nullable=True)

    service_line: Mapped[Optional[str]] = mapped_column(db.String(40), nullable=True)  # Ortho|Neuro|Geriatric|Sports|Pediatrics|Vestibular|Pelvic Health

    # Diagnoses (synthetic, ICD-10 formatted)
    primary_dx: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)    # Medical Dx
    secondary_dx: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    treatment_dx: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)  # PT Treatment Dx / impairment codes

    precautions: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    contraindications: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    case_summary: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    allergies: Mapped[List["Allergy"]] = relationship("Allergy", back_populates="patient", cascade="all, delete-orphan")
    medications: Mapped[List["Medication"]] = relationship("Medication", back_populates="patient", cascade="all, delete-orphan")
    problems: Mapped[List["Problem"]] = relationship("Problem", back_populates="patient", cascade="all, delete-orphan")
    encounters: Mapped[List["Encounter"]] = relationship("Encounter", back_populates="patient", cascade="all, delete-orphan")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="patient", cascade="all, delete-orphan")

    @property
    def display_name(self) -> str:
        return f"{self.last_name}, {self.first_name}"

    @property
    def age(self) -> int:
        today = date.today()
        years = today.year - self.dob.year
        if (today.month, today.day) < (self.dob.month, self.dob.day):
            years -= 1
        return years


class Allergy(db.Model):
    __tablename__ = "allergies"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("patients.id"), index=True, nullable=False)

    substance: Mapped[str] = mapped_column(db.String(120), nullable=False)
    reaction: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(db.String(40), nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="allergies")


class Medication(db.Model):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("patients.id"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    dose: Mapped[Optional[str]] = mapped_column(db.String(80), nullable=True)
    route: Mapped[Optional[str]] = mapped_column(db.String(40), nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(db.String(80), nullable=True)
    status: Mapped[str] = mapped_column(db.String(30), default="Active", nullable=False)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="medications")


class Problem(db.Model):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("patients.id"), index=True, nullable=False)

    description: Mapped[str] = mapped_column(db.String(255), nullable=False)
    status: Mapped[str] = mapped_column(db.String(30), default="Active", nullable=False)
    onset_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="problems")


class Encounter(db.Model):
    __tablename__ = "encounters"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("patients.id"), index=True, nullable=False)
    provider_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("users.id"), index=True, nullable=False)

    encounter_date: Mapped[datetime] = mapped_column(db.DateTime, default=now_utc, index=True, nullable=False)
    encounter_type: Mapped[str] = mapped_column(db.String(60), default="Daily Visit Note", nullable=False)

    location: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    status: Mapped[str] = mapped_column(db.String(30), default="Draft", nullable=False)  # Draft|Signed
    signed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    locked: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="encounters")
    provider: Mapped["User"] = relationship("User", back_populates="encounters")
    note: Mapped[Optional["Note"]] = relationship("Note", back_populates="encounter", uselist=False, cascade="all, delete-orphan")
    charges: Mapped[List["Charge"]] = relationship("Charge", back_populates="encounter", cascade="all, delete-orphan")


class Note(db.Model):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    encounter_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("encounters.id"), unique=True, index=True, nullable=False)

    # Supported templates: Evaluation | Daily | Progress | Discharge
    template: Mapped[str] = mapped_column(db.String(60), default="Daily", nullable=False)

    # Narrative sections (presented in UI as Subjective/Objective/Assessment/Plan but not labeled SOAP)
    subjective: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    objective: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    assessment: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    plan: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # Common structured fields
    pain_pre: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    pain_post: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    vitals_json = mapped_column(db.JSON, default=dict, nullable=False)   # {"bp":"120/78","hr":72,"spo2":98}
    outcome_json = mapped_column(db.JSON, default=dict, nullable=False)  # standardized outcomes, e.g., {"LEFS":45,"Berg":42}
    extra_json = mapped_column(db.JSON, default=dict, nullable=False)    # template-specific fields

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=now_utc, onupdate=now_utc, nullable=False)

    encounter: Mapped["Encounter"] = relationship("Encounter", back_populates="note")


class Appointment(db.Model):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("patients.id"), index=True, nullable=False)
    provider_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("users.id"), index=True, nullable=False)

    start_at: Mapped[datetime] = mapped_column(db.DateTime, index=True, nullable=False)
    end_at: Mapped[datetime] = mapped_column(db.DateTime, index=True, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)
    status: Mapped[str] = mapped_column(db.String(30), default="Scheduled", nullable=False)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="appointments")
    provider: Mapped["User"] = relationship("User", back_populates="appointments")


class Order(db.Model):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("patients.id"), index=True, nullable=False)

    ordered_at: Mapped[datetime] = mapped_column(db.DateTime, default=now_utc, nullable=False)
    description: Mapped[str] = mapped_column(db.String(255), nullable=False)
    status: Mapped[str] = mapped_column(db.String(30), default="Active", nullable=False)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="orders")


class Charge(db.Model):
    __tablename__ = "charges"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    encounter_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("encounters.id"), index=True, nullable=False)

    cpt_code: Mapped[str] = mapped_column(db.String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    minutes: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)  # minutes for the code (if timed)
    units: Mapped[int] = mapped_column(db.Integer, default=1, nullable=False)
    modifiers: Mapped[Optional[str]] = mapped_column(db.String(60), nullable=True)

    encounter: Mapped["Encounter"] = relationship("Encounter", back_populates="charges")


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    at: Mapped[datetime] = mapped_column(db.DateTime, default=now_utc, index=True, nullable=False)

    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("users.id"), index=True, nullable=False)
    patient_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey("patients.id"), index=True, nullable=True)
    encounter_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey("encounters.id"), index=True, nullable=True)

    action: Mapped[str] = mapped_column(db.String(80), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
