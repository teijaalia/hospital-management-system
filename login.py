from flask import Flask, request, jsonify
from sqlalchemy.orm import sessionmaker
from models import init_db, User

app = Flask(__name__)

engine = init_db()
Session = sessionmaker(bind=engine)

@app.post("/login")
def login():
    session = Session()
    data = request.json

    user = session.query(User).filter_by(Email=data["email"]).first()

    if not user or user.Password != data["password"]:
        return jsonify({"status": "error"}), 401

    # Select name according to a profile
    if user.User_Type.lower() == "patient" and user.patient_profile:
        name = f"{user.patient_profile.First_Name} {user.patient_profile.Last_Name}"
    elif user.User_Type.lower() == "doctor" and user.doctor_profile:
        name = f"{user.doctor_profile.First_Name} {user.doctor_profile.Last_Name}"
    elif user.User_Type.lower() == "admin" and user.admin_profile:
        name = f"{user.admin_profile.First_Name} {user.admin_profile.Last_Name}"
    else:
        name = user.Email  # fallback if profile not found

    return jsonify({
        "status": "ok",
        "name": name,
        "type": user.User_Type
    })