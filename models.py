from sqlalchemy import (
    create_engine, Column, Integer, String, Date, Time, Float, ForeignKey, Enum
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.types import Enum as SQLAEnum

Base = declarative_base()

# Enum for user types
USER_TYPES = ('patient', 'doctor', 'admin')

class User(Base):
    __tablename__ = 'user'

    User_ID = Column(Integer, primary_key=True)
    Email = Column(String(100), unique=True, nullable=False)
    Password = Column(String(100), nullable=False)
    User_Type = Column(SQLAEnum(*USER_TYPES, name="user_types"), nullable=False)

    # Relationships
    patient_profile = relationship("Patient", uselist=False, back_populates="user")
    doctor_profile = relationship("Doctor", uselist=False, back_populates="user")
    admin_profile = relationship("Administrator", uselist=False, back_populates="user")


class Patient(Base):
    __tablename__ = 'patient'

    Patient_ID = Column(Integer, ForeignKey('user.User_ID'), primary_key=True)
    First_Name = Column(String(50), nullable=False)
    Last_Name = Column(String(50), nullable=False)
    Address = Column(String(100))
    Phone = Column(String(20))
    Admission_Date = Column(Date)
    Discharge_Date = Column(Date)
    Condition = Column(String(255))

    user = relationship("User", back_populates="patient_profile")
    appointments = relationship("Appointment", back_populates="patient")
    medical_records = relationship("MedicalRecord", back_populates="patient")
    bills = relationship("Bill", back_populates="patient")


class Doctor(Base):
    __tablename__ = 'doctor'

    Doctor_ID = Column(Integer, ForeignKey('user.User_ID'), primary_key=True)
    First_Name = Column(String(50), nullable=False)
    Last_Name = Column(String(50), nullable=False)
    Specialization = Column(String(100))

    user = relationship("User", back_populates="doctor_profile")
    appointments = relationship("Appointment", back_populates="doctor")
    medical_records = relationship("MedicalRecord", back_populates="doctor")
    department = relationship("Department", back_populates="doctor", uselist=False)


class Administrator(Base):
    __tablename__ = 'administrator'

    Admin_ID = Column(Integer, ForeignKey('user.User_ID'), primary_key=True)
    First_Name = Column(String(50))
    Last_Name = Column(String(50))
    Dept_ID = Column(Integer, ForeignKey('department.Dept_ID'))

    user = relationship("User", back_populates="admin_profile")
    department = relationship("Department", back_populates="administrators")


class Appointment(Base):
    __tablename__ = 'appointment'

    Appt_ID = Column(Integer, primary_key=True)
    Doctor_ID = Column(Integer, ForeignKey('doctor.Doctor_ID'))
    Patient_ID = Column(Integer, ForeignKey('patient.Patient_ID'))
    Date = Column(Date)
    Time = Column(Time)
        
    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")


class MedicalRecord(Base):
    __tablename__ = 'medical_record'

    Record_ID = Column(Integer, primary_key=True)
    Patient_ID = Column(Integer, ForeignKey('patient.Patient_ID'))
    Doctor_ID = Column(Integer, ForeignKey('doctor.Doctor_ID'))
    Diagnosis = Column(String(255))
    Symptoms = Column(String(255))

    patient = relationship("Patient", back_populates="medical_records")
    doctor = relationship("Doctor", back_populates="medical_records")
    treatments = relationship("Treatment", back_populates="medical_record")


class Treatment(Base):
    __tablename__ = 'treatment'

    Treatment_ID = Column(Integer, primary_key=True)
    Medicine = Column(String(100))
    Prescription = Column(String(255))
    Record_ID = Column(Integer, ForeignKey('medical_record.Record_ID'))

    medical_record = relationship("MedicalRecord", back_populates="treatments")


class Bill(Base):
    __tablename__ = 'bill'

    Payment_ID = Column(Integer, primary_key=True)
    Patient_ID = Column(Integer, ForeignKey('patient.Patient_ID'))
    Date = Column(Date)
    Cost = Column(Float)
    Paid = Column(String(3))
    
    patient = relationship("Patient", back_populates="bills")


class Department(Base):
    __tablename__ = 'department'

    Dept_ID = Column(Integer, primary_key=True)
    Dept_name = Column(String(100))
    Dept_head = Column(String(100))
    Doctor_ID = Column(Integer, ForeignKey('doctor.Doctor_ID'))

    doctor = relationship("Doctor", back_populates="department")
    administrators = relationship("Administrator", back_populates="department")

class Room(Base):
    __tablename__ = 'room'

    Room_ID = Column(Integer, primary_key=True)
    Appt_ID = Column(Integer, ForeignKey('appointment.Appt_ID'))
    room_type = Column(String(50))

    appointment = relationship("Appointment", backref="room")

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()

# CREATE
def add_user(session, email, password, user_type):
    new_user = User(Email=email, Password=password, User_Type=user_type)
    session.add(new_user)
    session.commit()
    return new_user

# READ
def get_user_by_email(session, email):
    return session.query(User).filter_by(Email=email).first()

# UPDATE
def update_user_password(session, user_id, new_password):
    user = session.query(User).filter_by(User_ID=user_id).first()
    if user:
        user.Password = new_password
        session.commit()
    return user

# DELETE
def delete_user(session, user_id):
    user = session.query(User).filter_by(User_ID=user_id).first()
    if user:
        session.delete(user)
        session.commit()


# ---------------------------
# DATABASE INITIALIZATION
# ---------------------------

def init_db():
    """Creates database and all tables."""
    engine = create_engine('sqlite:///hospital.db')
    Base.metadata.create_all(engine)
    return engine

engine = init_db()
Session = sessionmaker(bind=engine)
session = Session()
