from sqlalchemy.orm import sessionmaker
from models import (
    Base,
    init_db,
    User,
    Administrator,
    Doctor,
    Patient,
    Appointment,
    Room,
    Treatment,
    MedicalRecord,
    Bill,
    Department,
)
from datetime import date, time, datetime
import os
import csv
from sqlalchemy import text

# Creates a connection to database
engine = init_db()
Session = sessionmaker(bind=engine)
session = Session()

# Ensure schema quirks (idempotent migrations)
def ensure_bill_paid_column():
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("PRAGMA table_info(bill)")).fetchall()
            has_paid = any(r[1] == "Paid" for r in rows)
            if not has_paid:
                conn.exec_driver_sql("ALTER TABLE bill ADD COLUMN Paid VARCHAR(3)")
    except Exception:
        # Best-effort; if this fails, later operations may still work if column exists
        pass

ensure_bill_paid_column()

# -----------------------------
# Helper functions (idempotent creators)
# -----------------------------
def ensure_user(email, password, user_type):
    user = session.query(User).filter(User.Email == email).first()
    if user:
        return user
    user = User(Email=email, Password=password, User_Type=user_type)
    session.add(user)
    session.flush()
    return user


def ensure_admin(user, first_name, last_name, dept_id=None):
    admin = session.query(Administrator).filter(Administrator.Admin_ID == user.User_ID).first()
    if admin:
        return admin
    admin = Administrator(
        Admin_ID=user.User_ID,
        First_Name=first_name,
        Last_Name=last_name,
        Dept_ID=dept_id,
    )
    session.add(admin)
    session.flush()
    return admin


def ensure_doctor(user, first_name, last_name, specialization):
    doctor = session.query(Doctor).filter(Doctor.Doctor_ID == user.User_ID).first()
    if doctor:
        return doctor
    doctor = Doctor(
        Doctor_ID=user.User_ID,
        First_Name=first_name,
        Last_Name=last_name,
        Specialization=specialization,
    )
    session.add(doctor)
    session.flush()
    return doctor


def ensure_patient(user, first_name, last_name, address, phone, condition, admission=None, discharge=None):
    patient = session.query(Patient).filter(Patient.Patient_ID == user.User_ID).first()
    if patient:
        return patient
    patient = Patient(
        Patient_ID=user.User_ID,
        First_Name=first_name,
        Last_Name=last_name,
        Address=address,
        Phone=phone,
        Admission_Date=admission,
        Discharge_Date=discharge,
        Condition=condition,
    )
    session.add(patient)
    session.flush()
    return patient


def ensure_department(name, head, doctor_id=None):
    dept = session.query(Department).filter(Department.Dept_name == name).first()
    if dept:
        return dept
    dept = Department(
        Dept_name=name,
        Dept_head=head,
        Doctor_ID=doctor_id,
    )
    session.add(dept)
    session.flush()
    return dept


def ensure_appointment(doctor_id, patient_id, appt_date, appt_time):
    appt = (
        session.query(Appointment)
        .filter(
            Appointment.Doctor_ID == doctor_id,
            Appointment.Patient_ID == patient_id,
            Appointment.Date == appt_date,
            Appointment.Time == appt_time,
        )
        .first()
    )
    if appt:
        return appt
    appt = Appointment(
        Doctor_ID=doctor_id,
        Patient_ID=patient_id,
        Date=appt_date,
        Time=appt_time,
    )
    session.add(appt)
    session.flush()
    return appt


def ensure_room(appt_id, room_type):
    room = session.query(Room).filter(Room.Appt_ID == appt_id).first()
    if room:
        return room
    room = Room(Appt_ID=appt_id, room_type=room_type)
    session.add(room)
    session.flush()
    return room


def ensure_medical_record(patient_id, doctor_id, diagnosis, symptoms=None):
    # Find by key fields first (avoid dupes regardless of symptoms)
    record = (
        session.query(MedicalRecord)
        .filter(
            MedicalRecord.Patient_ID == patient_id,
            MedicalRecord.Doctor_ID == doctor_id,
            MedicalRecord.Diagnosis == diagnosis,
        )
        .first()
    )
    if record:
        # Backfill symptoms if missing
        if symptoms and (not getattr(record, "Symptoms", None)):
            record.Symptoms = symptoms
            session.flush()
        return record
    record = MedicalRecord(
        Patient_ID=patient_id,
        Doctor_ID=doctor_id,
        Diagnosis=diagnosis,
        Symptoms=symptoms,
    )
    session.add(record)
    session.flush()
    return record


def ensure_treatment(record_id, medicine, prescription):
    treatment = (
        session.query(Treatment)
        .filter(
            Treatment.Record_ID == record_id,
            Treatment.Medicine == medicine,
            Treatment.Prescription == prescription,
        )
        .first()
    )
    if treatment:
        return treatment
    treatment = Treatment(
        Record_ID=record_id,
        Medicine=medicine,
        Prescription=prescription,
    )
    session.add(treatment)
    session.flush()
    return treatment


def ensure_bill(patient_id, bill_date, cost, paid=None):
    bill = (
        session.query(Bill)
        .filter(
            Bill.Patient_ID == patient_id,
            Bill.Date == bill_date,
            Bill.Cost == cost,
        )
        .first()
    )
    if bill:
        return bill
    bill = Bill(
        Patient_ID=patient_id,
        Date=bill_date,
        Cost=cost,
        Paid=paid,
    )
    session.add(bill)
    session.flush()
    return bill


# -----------------------------
# Loading helpers
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_DIR = os.path.join(BASE_DIR, "seed_data")


def read_rows(file_name):
    """
    Reads CSV-with-headers from seed_data/<file_name>.
    - Supports .txt or .csv naming (prefers .txt).
    - Ignores empty lines and lines starting with '#'
    Returns list[dict]. Missing file -> empty list.
    """
    candidates = [
        os.path.join(SEED_DIR, f"{file_name}.txt"),
        os.path.join(SEED_DIR, f"{file_name}.csv"),
    ]
    path = next((p for p in candidates if os.path.exists(p)), None)
    if not path:
        return []

    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        # Filter comments/blank lines while retaining CSV parsing
        filtered = [line for line in fh if line.strip() and not line.lstrip().startswith("#")]
        if not filtered:
            return []
        reader = csv.DictReader(filtered)
        for raw in reader:
            # strip whitespace from keys/values
            row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in raw.items() if k is not None}
            rows.append(row)
    return rows


def parse_date(value):
    if not value:
        return None
    # Accept YYYY-MM-DD
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_time(value):
    if not value:
        return None
    # Accept HH:MM (24h)
    return datetime.strptime(value, "%H:%M").time()


def to_float(value):
    if value is None or value == "":
        return None
    return float(value)


# -----------------------------
# Seed from files (order matters due to FKs)
# -----------------------------
# 1) Users
for row in read_rows("users"):
    ensure_user(
        email=row.get("Email"),
        password=row.get("Password"),
        user_type=row.get("User_Type"),
    )

session.flush()

# Build quick lookup maps by email
email_to_user = {u.Email: u for u in session.query(User).all()}

# 2) Doctors
for row in read_rows("doctors"):
    email = row.get("Email")
    user = email_to_user.get(email) or ensure_user(email=email, password=row.get("Password", ""), user_type="doctor")
    email_to_user[email] = user
    ensure_doctor(
        user=user,
        first_name=row.get("First_Name"),
        last_name=row.get("Last_Name"),
        specialization=row.get("Specialization"),
    )

# 3) Patients
for row in read_rows("patients"):
    email = row.get("Email")
    user = email_to_user.get(email) or ensure_user(email=email, password=row.get("Password", ""), user_type="patient")
    email_to_user[email] = user
    ensure_patient(
        user=user,
        first_name=row.get("First_Name"),
        last_name=row.get("Last_Name"),
        address=row.get("Address"),
        phone=row.get("Phone"),
        condition=row.get("Condition"),
        admission=parse_date(row.get("Admission_Date")),
        discharge=parse_date(row.get("Discharge_Date")),
    )

# 4) Administrators
for row in read_rows("administrators"):
    email = row.get("Email")
    user = email_to_user.get(email) or ensure_user(email=email, password=row.get("Password", ""), user_type="admin")
    email_to_user[email] = user
    ensure_admin(
        user=user,
        first_name=row.get("First_Name"),
        last_name=row.get("Last_Name"),
        dept_id=None,  # optionally linked after departments
    )

session.flush()

# Build role maps
doctor_email_to_id = {d.user.Email: d.Doctor_ID for d in session.query(Doctor).all() if d.user}
patient_email_to_id = {p.user.Email: p.Patient_ID for p in session.query(Patient).all() if p.user}

# 5) Departments
for row in read_rows("departments"):
    doc_email = row.get("Doctor_Email")
    doc_id = doctor_email_to_id.get(doc_email) if doc_email else None
    ensure_department(
        name=row.get("Dept_name") or row.get("Name"),
        head=row.get("Dept_head") or row.get("Head"),
        doctor_id=doc_id,
    )

session.flush()

# Optionally link admins to departments if provided in file
dept_name_to_dept = {d.Dept_name: d for d in session.query(Department).all()}
for row in read_rows("administrators"):
    email = row.get("Email")
    dept_name = row.get("Dept_name") or row.get("Dept")
    if not dept_name:
        continue
    user = email_to_user.get(email)
    dept = dept_name_to_dept.get(dept_name)
    if user and dept:
        admin = session.query(Administrator).filter(Administrator.Admin_ID == user.User_ID).first()
        if admin and admin.Dept_ID != dept.Dept_ID:
            admin.Dept_ID = dept.Dept_ID
            session.flush()

# 6) Appointments
for row in read_rows("appointments"):
    doc_email = row.get("Doctor_Email")
    pat_email = row.get("Patient_Email")
    d_id = doctor_email_to_id.get(doc_email)
    p_id = patient_email_to_id.get(pat_email)
    if not d_id or not p_id:
        continue
    appt = ensure_appointment(
        doctor_id=d_id,
        patient_id=p_id,
        appt_date=parse_date(row.get("Date")),
        appt_time=parse_time(row.get("Time")),
    )

# Map to find appointment by composite values for room linking
def find_appointment_id(doctor_id, patient_id, appt_date, appt_time):
    appt = (
        session.query(Appointment)
        .filter(
            Appointment.Doctor_ID == doctor_id,
            Appointment.Patient_ID == patient_id,
            Appointment.Date == appt_date,
            Appointment.Time == appt_time,
        )
        .first()
    )
    return appt.Appt_ID if appt else None

# 7) Rooms
for row in read_rows("rooms"):
    doc_email = row.get("Doctor_Email")
    pat_email = row.get("Patient_Email")
    d_id = doctor_email_to_id.get(doc_email)
    p_id = patient_email_to_id.get(pat_email)
    appt_date = parse_date(row.get("Date"))
    appt_time = parse_time(row.get("Time"))
    appt_id = find_appointment_id(d_id, p_id, appt_date, appt_time) if d_id and p_id else None
    if appt_id:
        ensure_room(appt_id, row.get("room_type") or row.get("Room_Type"))

# 8) Medical Records
for row in read_rows("medical_records"):
    doc_email = row.get("Doctor_Email")
    pat_email = row.get("Patient_Email")
    d_id = doctor_email_to_id.get(doc_email)
    p_id = patient_email_to_id.get(pat_email)
    if not d_id or not p_id:
        continue
    ensure_medical_record(
        patient_id=p_id,
        doctor_id=d_id,
        diagnosis=row.get("Diagnosis"),
        symptoms=row.get("Symptoms"),
    )

# 9) Treatments
for row in read_rows("treatments"):
    doc_email = row.get("Doctor_Email")
    pat_email = row.get("Patient_Email")
    diagnosis = row.get("Diagnosis")
    d_id = doctor_email_to_id.get(doc_email)
    p_id = patient_email_to_id.get(pat_email)
    if not d_id or not p_id:
        continue
    record = ensure_medical_record(p_id, d_id, diagnosis)
    ensure_treatment(
        record_id=record.Record_ID,
        medicine=row.get("Medicine"),
        prescription=row.get("Prescription") or row.get("Perscription"),
    )

# 10) Bills
for row in read_rows("bills"):
    pat_email = row.get("Patient_Email")
    p_id = patient_email_to_id.get(pat_email)
    if not p_id:
        continue
    ensure_bill(
        patient_id=p_id,
        bill_date=parse_date(row.get("Date")),
        cost=to_float(row.get("Cost")),
        paid=row.get("Paid"),
    )

# -----------------------------
# Save all
# -----------------------------
session.commit()
