from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from models import User, Patient, Doctor, Administrator, Appointment, Room, Treatment, Bill, MedicalRecord, Department, session as db_session
from datetime import datetime, timedelta, time
from sqlalchemy import func
import os


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

# --- LOGIN API (POST) ---
@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = db_session.query(User).filter(User.Email == email).first()
    if not user or user.Password != password:
        return render_template("index.html", error="Email or password is incorrect")

    session["user_id"] = user.User_ID
    session["user_type"] = user.User_Type.lower()

    if session["user_type"] == "patient" and user.patient_profile:
        session["patient_id"] = user.patient_profile.Patient_ID
        return redirect(url_for("patient_page", patient_id=user.patient_profile.Patient_ID))
    elif session["user_type"] == "doctor" and user.doctor_profile:
        session["doctor_id"] = user.doctor_profile.Doctor_ID
        return redirect(url_for("doctor_page", doctor_id=user.doctor_profile.Doctor_ID))
    elif session["user_type"] == "admin" and user.admin_profile:
        session["admin_id"] = user.admin_profile.Admin_ID
        return redirect(url_for("admin_page", admin_id=user.admin_profile.Admin_ID))

    return "User logged in: " + user.User_Type

# --- MAIN PAGE ---
@app.route("/")
def index():
    return render_template("index.html", error=None)

# --- SIGN UP PAGE ---

@app.route("/signup", methods=["GET"])
def signup_page():
    return render_template("signup.html")

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json 

    email = data.get("email")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    address = data.get("address")
    phone = data.get("phone")

    # Check if email exists
    existing = db_session.query(User).filter_by(Email=email).first()
    if existing:
        return jsonify({"status": "error", "message": "Email already exists"}), 400

    # Create user (ALWAYS patient)
    new_user = User(
        Email=email,
        Password=password,
        User_Type="patient"
    )
    db_session.add(new_user)
    db_session.commit()

    # Create patient profile
    profile = Patient(
        Patient_ID=new_user.User_ID,
        First_Name=first_name,
        Last_Name=last_name,
        Address=address,
        Phone=phone
    )
    db_session.add(profile)
    db_session.commit()

    return jsonify({"status": "ok"})

# --- EDIT PROFILE PAGE ---
@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    user_type = session.get("user_type", "").lower()

    user = db_session.query(User).filter(User.User_ID == user_id).first()

    if user_type == "patient":
        patient = db_session.query(Patient).filter(Patient.Patient_ID == user_id).first()
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            address = request.form.get("address", "").strip()
            phone = request.form.get("phone", "").strip()

            if email:
                user.Email = email
            if first_name:
                patient.First_Name = first_name
            if last_name:
                patient.Last_Name = last_name
            patient.Address = address
            patient.Phone = phone

            db_session.commit()
            return redirect(url_for("profile"))

        return render_template("editProfile.html", user=user, patient=patient)
    
    return redirect(url_for("profile"))



# --- PATIENT PAGE ---
@app.route("/patient/<int:patient_id>")
def patient_page(patient_id):
    if "patient_id" not in session or session["patient_id"] != patient_id:
        return redirect(url_for("index"))

    patient = db_session.query(Patient).filter(Patient.Patient_ID == patient_id).first()
    if not patient:
        return "Patient not found", 404

    return render_template("patient.html", patient=patient)

# --- USER PROFILE PAGES ---
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]
    user_type = session.get("user_type", "").lower()

    user = db_session.query(User).filter(User.User_ID == user_id).first()

    user_id = session["user_id"]
    user_type = session.get("user_type", "").lower()

    user = db_session.query(User).filter(User.User_ID == user_id).first()

    if user_type == "patient":
        return render_template("patientFrontPage.html", user=user, patient=user.patient_profile)
    elif user_type == "doctor":
        return render_template("doctorFrontPage.html", user=user, doctor=user.doctor_profile)
    elif user_type == "admin":
        return render_template("adminFrontPage.html", user=user, admin=user.admin_profile)

    return redirect("/")

# --- DOCTOR PAGE --- 
@app.route("/doctor/<int:doctor_id>")
def doctor_page(doctor_id):
    if "doctor_id" not in session or session["doctor_id"] != doctor_id:
        return redirect(url_for("index"))

    # get doctor from database
    doctor = db_session.query(Doctor).filter(Doctor.Doctor_ID == doctor_id).first()
    if not doctor:
        return "Doctor not found", 404
    return render_template("doctor.html", doctor=doctor)

# --- ADMINISTRATOR PAGE ---
@app.route("/admin/<int:admin_id>")
def admin_page(admin_id):
    if "admin_id" not in session or session["admin_id"] != admin_id:
        return redirect(url_for("index"))

    # get admin from database
    admin = db_session.query(Administrator).filter(Administrator.Admin_ID == admin_id).first()
    if not admin:
        return "Admin not found", 404
    return render_template("administrator.html", administrator=admin)

# --- LOGOUT ---
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# --- Convenient 'back to home' function ---
@app.route("/home")
def home():
    user_type = session.get("user_type", "").lower()

    if user_type == "patient" and session.get("patient_id"):
        return redirect(url_for("patient_page", patient_id=session["patient_id"]))
    if user_type == "doctor" and session.get("doctor_id"):
        return redirect(url_for("doctor_page", doctor_id=session["doctor_id"]))
    if user_type == "admin" and session.get("admin_id"):
        return redirect(url_for("admin_page", admin_id=session["admin_id"]))

    # Fallback: not logged in or missing ids
    return redirect(url_for("index"))


# --- ViewRecords PAGE ---
@app.route("/ViewRecords")
def ViewRecords_self():
    if "admin_id" not in session:
        return redirect(url_for("index"))

    admin_id = session["admin_id"]
    admin = db_session.query(Administrator).filter(Administrator.Admin_ID == admin_id).first()
    if not admin:
        return "Admin not found", 404
    return render_template("ViewRecords.html", administrator=admin)

# --- Appointment View PAGE ---
@app.route("/AppointmentView/<int:user_id>")
def AppointmentView(user_id):
    if "user_id" not in session or session["user_id"] != user_id:
        return redirect("/")

    user_id = session["user_id"]
    user_type = session.get("user_type", "").lower()

    user = db_session.query(User).filter(User.User_ID == user_id).first()

    # Fetch appointments based on role
    appointments = []
    if user_type == "patient":
        #patientID = db_session.query(Patient).filter(Patient.User_ID == user_id)
        appointments = db_session.query(Appointment).filter(Appointment.Patient_ID == user_id).all()
    elif user_type == "doctor":
        appointments = db_session.query(Appointment).filter(Appointment.Doctor_ID == user_id).all()
    elif user_type == "admin":
        # Admins see all appointments
        appointments = db_session.query(Appointment).all()

    return render_template("AppointmentView.html", user=user, user_type=user_type, appointments=appointments)

# --- Bill View ---
@app.route("/BillView/<int:user_id>")
def BillView(user_id):
    if "user_id" not in session or session["user_id"] != user_id:
        return redirect("/")

    user_id = session["user_id"]
    user_type = session.get("user_type", "").lower()

    user = db_session.query(User).filter(User.User_ID == user_id).first()

    # Fetch appointments based on role
    bills = []
    if user_type == "patient":
        bills = db_session.query(Bill).filter(Bill.Patient_ID == user_id).all()

        return render_template("BillView.html", user=user, user_type=user_type, bill_list=bills)

@app.route("/MedicalRecords/<int:user_id>")
def MedicalRecords(user_id):
    if "user_id" not in session or session["user_id"] != user_id:
        return redirect("/")

    user_id = session["user_id"]
    user_type = session.get("user_type", "").lower()

    user = db_session.query(User).filter(User.User_ID == user_id).first()

    # Fetch appointments based on role
    records = []
    if user_type == "patient":
        records = db_session.query(MedicalRecord).filter(MedicalRecord.Patient_ID == user_id).all()
    elif user_type == "doctor":
        records = db_session.query(MedicalRecord).filter(MedicalRecord.Doctor_ID == user_id).all()

    return render_template("MedicalRecords.html", user=user, user_type=user_type, records_list=records)

# --- Request Appointment Page ---
@app.route("/RequestAppointment")
def RequestAppointment():
    return render_template("RequestAppointment.html")

# --- Requests ---
@app.get("/api/patients")
def api_patients():
    patients = db_session.query(Patient).all()
    data = [
        {
            "Patient_ID": p.Patient_ID,
            "First_Name": p.First_Name,
            "Last_Name": p.Last_Name,
        }
        for p in patients
    ]
    response = jsonify(data)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.get("/api/doctors")
def api_doctors():
    doctors = db_session.query(Doctor).all()
    data = [
        {
            "Doctor_ID": d.Doctor_ID,
            "First_Name": d.First_Name,
            "Last_Name": d.Last_Name,
            "Specialization": d.Specialization,
        }
        for d in doctors
    ]
    response = jsonify(data)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.get("/api/appointments")
def api_appointments():
    appointments = db_session.query(Appointment).all()
    def serialize_dt(value):
        return str(value) if value is not None else None
    data = [
        {
            "Appt_ID": a.Appt_ID,
            "Doctor_ID": a.Doctor_ID,
            "Patient_ID": a.Patient_ID,
            "Date": serialize_dt(a.Date),
            "Time": serialize_dt(a.Time),
        }
        for a in appointments
    ]
    response = jsonify(data)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.get("/api/rooms")
def api_rooms():
    rooms = db_session.query(Room).all()
    data = [
        {
            "Room_ID": r.Room_ID,
            "Appt_ID": r.Appt_ID,
            "room_type": r.room_type,
        }
        for r in rooms
    ]
    response = jsonify(data)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.get("/api/treatments")
def api_treatments():
    treatments = db_session.query(Treatment).all()
    # Note: frontend expects 'Perscription' (misspelling), so we output that key
    data = [
        {
            "Treatment_ID": t.Treatment_ID,
            "Medicine": t.Medicine,
            "Perscription": t.Prescription,
        }
        for t in treatments
    ]
    response = jsonify(data)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

# --- Additional APIs for ViewRecords page ---
@app.get("/api/users")
def api_users():
    users = db_session.query(User).all()
    data = [
        {
            "User_ID": u.User_ID,
            "Email": u.Email,
            "User_Type": u.User_Type,
            "Password": u.Password
        }
        for u in users
    ]
    response = jsonify(data)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.get("/api/administrators")
def api_administrators():
    admins = db_session.query(Administrator).all()
    data = [
        {
            "Admin_ID": a.Admin_ID,
            "First_Name": a.First_Name,
            "Last_Name": a.Last_Name,
            "Dept_ID": a.Dept_ID,
        }
        for a in admins
    ]
    response = jsonify(data)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.get("/api/departments")
def api_departments():
    depts = db_session.query(Department).all()
    data = [
        {
            "Dept_ID": d.Dept_ID,
            "Dept_name": d.Dept_name,
            "Dept_head": d.Dept_head,
            "Doctor_ID": d.Doctor_ID,
        }
        for d in depts
    ]
    response = jsonify(data)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.get("/api/medical_records")
def api_medical_records():
    records = db_session.query(MedicalRecord).all()
    data = [
        {
            "Record_ID": r.Record_ID,
            "Patient_ID": r.Patient_ID,
            "Doctor_ID": r.Doctor_ID,
            "Symptoms": getattr(r, "Symptoms", None),
            "Diagnosis": r.Diagnosis,
        }
        for r in records
    ]
    response = jsonify(data)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.get("/api/bills")
def api_bills():
    bills = db_session.query(Bill).all()
    def serialize_dt(value):
        return str(value) if value is not None else None
    data = [
        {
            "Payment_ID": b.Payment_ID,
            "Patient_ID": b.Patient_ID,
            "Date": serialize_dt(b.Date),
            "Cost": b.Cost,
            "Paid": b.Paid,
        }
        for b in bills
    ]
    response = jsonify(data)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

# --- Create/Update records (generic) ---
@app.post("/api/records/<string:rtype>")
def api_records_mutation(rtype: str):
    data = request.json or {}
    rtype = (rtype or "").strip()

    def next_id(model, id_attr):
        current = db_session.query(getattr(model, id_attr)).order_by(getattr(model, id_attr).desc()).first()
        return (current[0] + 1) if current and current[0] is not None else 1

    def parse_date(v):
        if not v:
            return None
        return datetime.strptime(v, "%Y-%m-%d").date()

    def parse_time(v):
        if not v:
            return None
        return datetime.strptime(v, "%H:%M").time()

    # Users
    if rtype == "Users":
        user_id = data.get("User_ID")
        user = db_session.query(User).filter(User.User_ID == user_id).first() if user_id else None
        allowed_types = {"patient", "doctor", "admin"}
        provided_type = (data.get("User_Type") or "").strip().lower()

        if user:
            email = (data.get("Email") or "").strip()
            if email:
                user.Email = email
            if provided_type in allowed_types:
                user.User_Type = provided_type
            pwd = data.get("Password")
            if pwd is not None and pwd != "":
                user.Password = pwd
            db_session.commit()
            return jsonify({"status": "updated", "User_ID": user.User_ID})
        # create
        new_user = User(
            Email=(data.get("Email") or "").strip(),
            Password=(data.get("Password") or ""),
            User_Type=(provided_type if provided_type in allowed_types else "patient"),
        )
        db_session.add(new_user)
        db_session.commit()
        return jsonify({"status": "created", "User_ID": new_user.User_ID})

    # Departments
    elif rtype == "Departments":
        dept_id = data.get("Dept_ID")
        dept = db_session.query(Department).filter(Department.Dept_ID == dept_id).first() if dept_id else None
        if dept:
            dept.Dept_name = data.get("Dept_name", dept.Dept_name)
            dept.Dept_head = data.get("Dept_head", dept.Dept_head)
            dept.Doctor_ID = data.get("Doctor_ID", dept.Doctor_ID)
            db_session.commit()
            return jsonify({"status": "updated", "Dept_ID": dept.Dept_ID})
        new_dept = Department(
            Dept_ID=next_id(Department, "Dept_ID"),
            Dept_name=data.get("Dept_name"),
            Dept_head=data.get("Dept_head"),
            Doctor_ID=data.get("Doctor_ID"),
        )
        db_session.add(new_dept)
        db_session.commit()
        return jsonify({"status": "created", "Dept_ID": new_dept.Dept_ID})

    # Medical Records
    elif rtype == "MedicalRecords":
        record_id = data.get("Record_ID")
        rec = db_session.query(MedicalRecord).filter(MedicalRecord.Record_ID == record_id).first() if record_id else None
        if rec:
            rec.Patient_ID = data.get("Patient_ID", rec.Patient_ID)
            rec.Doctor_ID = data.get("Doctor_ID", rec.Doctor_ID)
            if "Symptoms" in data:
                rec.Symptoms = data.get("Symptoms")
            rec.Diagnosis = data.get("Diagnosis", rec.Diagnosis)
            db_session.commit()
            return jsonify({"status": "updated", "Record_ID": rec.Record_ID})
        new_rec = MedicalRecord(
            Record_ID=next_id(MedicalRecord, "Record_ID"),
            Patient_ID=data.get("Patient_ID"),
            Doctor_ID=data.get("Doctor_ID"),
            Symptoms=data.get("Symptoms"),
            Diagnosis=data.get("Diagnosis"),
        )
        db_session.add(new_rec)
        db_session.commit()
        return jsonify({"status": "created", "Record_ID": new_rec.Record_ID})

    # Appointments
    elif rtype == "Appointments":
        appt_id = data.get("Appt_ID")
        appt = db_session.query(Appointment).filter(Appointment.Appt_ID == appt_id).first() if appt_id else None
        if appt:
            appt.Doctor_ID = data.get("Doctor_ID", appt.Doctor_ID)
            appt.Patient_ID = data.get("Patient_ID", appt.Patient_ID)
            appt.Date = parse_date(data.get("Date")) or appt.Date
            appt.Time = parse_time(data.get("Time")) or appt.Time
            db_session.commit()
            return jsonify({"status": "updated", "Appt_ID": appt.Appt_ID})
        new_appt = Appointment(
            Doctor_ID=data.get("Doctor_ID"),
            Patient_ID=data.get("Patient_ID"),
            Date=parse_date(data.get("Date")),
            Time=parse_time(data.get("Time")),
        )
        db_session.add(new_appt)
        db_session.commit()
        return jsonify({"status": "created", "Appt_ID": new_appt.Appt_ID})

    # Rooms
    elif rtype == "Rooms":
        room_id = data.get("Room_ID")
        room = db_session.query(Room).filter(Room.Room_ID == room_id).first() if room_id else None
        if room:
            room.Appt_ID = data.get("Appt_ID", room.Appt_ID)
            room.room_type = data.get("room_type", room.room_type)
            db_session.commit()
            return jsonify({"status": "updated", "Room_ID": room.Room_ID})
        new_room = Room(
            Appt_ID=data.get("Appt_ID"),
            room_type=data.get("room_type"),
        )
        db_session.add(new_room)
        db_session.commit()
        return jsonify({"status": "created", "Room_ID": new_room.Room_ID})

    # Treatments
    elif rtype == "Treatments":
        treatment_id = data.get("Treatment_ID")
        tr = db_session.query(Treatment).filter(Treatment.Treatment_ID == treatment_id).first() if treatment_id else None
        if tr:
            tr.Record_ID = data.get("Record_ID", tr.Record_ID)
            tr.Medicine = data.get("Medicine", tr.Medicine)
            tr.Prescription = data.get("Prescription", tr.Prescription)
            db_session.commit()
            return jsonify({"status": "updated", "Treatment_ID": tr.Treatment_ID})
        new_tr = Treatment(
            Record_ID=data.get("Record_ID"),
            Medicine=data.get("Medicine"),
            Prescription=data.get("Prescription"),
        )
        db_session.add(new_tr)
        db_session.commit()
        return jsonify({"status": "created", "Treatment_ID": new_tr.Treatment_ID})

    # Bills
    elif rtype == "Bills":
        payment_id = data.get("Payment_ID")
        b = db_session.query(Bill).filter(Bill.Payment_ID == payment_id).first() if payment_id else None
        if b:
            b.Patient_ID = data.get("Patient_ID", b.Patient_ID)
            b.Date = parse_date(data.get("Date")) or b.Date
            b.Cost = float(data.get("Cost")) if data.get("Cost") not in (None, "") else b.Cost
            if "Paid" in data:
                b.Paid = data.get("Paid")
            db_session.commit()
            return jsonify({"status": "updated", "Payment_ID": b.Payment_ID})
        new_b = Bill(
            Patient_ID=data.get("Patient_ID"),
            Date=parse_date(data.get("Date")),
            Cost=float(data.get("Cost")) if data.get("Cost") not in (None, "") else 0.0,
            Paid=data.get("Paid"),
        )
        db_session.add(new_b)
        db_session.commit()
        return jsonify({"status": "created", "Payment_ID": new_b.Payment_ID})
    else:
        return jsonify({"error": "Unsupported type"}), 400

@app.post("/api/appointments/auto")
def api_appointments_auto():
    # Must be logged in as patient
    if "user_id" not in session or session.get("user_type", "").lower() != "patient":
        return jsonify({"error": "Unauthorized"}), 401
    patient_id = session.get("patient_id") or session.get("user_id")

    # Pick the doctor with the fewest total appointments (fair load distribution)
    doctor_row = (
        db_session.query(Doctor, func.count(Appointment.Appt_ID).label("num_appts"))
        .outerjoin(Appointment, Doctor.Doctor_ID == Appointment.Doctor_ID)
        .group_by(Doctor.Doctor_ID)
        .order_by(func.count(Appointment.Appt_ID).asc(), Doctor.Doctor_ID.asc())
        .first()
    )
    doctor = doctor_row[0] if doctor_row else None
    if not doctor:
        return jsonify({"error": "No doctors available"}), 400

    # Start searching 3 days from now
    appt_date = (datetime.utcnow() + timedelta(days=3)).date()

    # Search business hours: 09:00 - 16:00, on the earliest day with a free slot
    max_days_ahead = 60
    chosen_date = None
    chosen_time = None
    for offset in range(0, max_days_ahead + 1):
        candidate_date = appt_date + timedelta(days=offset)
        for hour in range(9, 17):  # 09:00 to 16:00 inclusive
            candidate_time = time(hour, 0)
            doctor_busy = (
                db_session.query(Appointment)
                .filter(
                    Appointment.Doctor_ID == doctor.Doctor_ID,
                    Appointment.Date == candidate_date,
                    Appointment.Time == candidate_time,
                )
                .first()
            )
            if doctor_busy:
                continue
            patient_busy = (
                db_session.query(Appointment)
                .filter(
                    Appointment.Patient_ID == patient_id,
                    Appointment.Date == candidate_date,
                    Appointment.Time == candidate_time,
                )
                .first()
            )
            if patient_busy:
                continue
            chosen_date = candidate_date
            chosen_time = candidate_time
            break
        if chosen_date is not None:
            break

    if chosen_date is None:
        return jsonify({"error": "No available slots"}), 409

    appt = Appointment(
        Doctor_ID=doctor.Doctor_ID,
        Patient_ID=patient_id,
        Date=chosen_date,
        Time=chosen_time,
    )
    db_session.add(appt)
    db_session.commit()

    doctor_name = f"{doctor.First_Name} {doctor.Last_Name}"
    return jsonify({
        "status": "created",
        "Appt_ID": appt.Appt_ID,
        "Doctor_ID": doctor.Doctor_ID,
        "Doctor_Name": doctor_name,
        "Date": str(chosen_date),
        "Time": chosen_time.strftime("%H:%M"),
    })

if __name__ == "__main__":
    app.run(debug=True)
