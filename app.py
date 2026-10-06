import os
import sqlite3
from datetime import date

import streamlit as st
import ollama
from dotenv import load_dotenv

# --------------------------------------------------
# Load environment variables
# --------------------------------------------------

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="AI Hospital Assistant",
    page_icon="🏥",
    layout="wide"
)

# --------------------------------------------------
# Database
# --------------------------------------------------

DB_NAME = "hospital.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Doctors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            specialization TEXT NOT NULL,
            available_days TEXT NOT NULL,
            fee INTEGER NOT NULL
        )
    """)

    # Appointments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            doctor_name TEXT NOT NULL,
            department TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL
        )
    """)

    # Add sample doctors only if table is empty
    cursor.execute("SELECT COUNT(*) FROM doctors")
    count = cursor.fetchone()[0]

    if count == 0:
        doctors = [
            (
                "Dr. Anil Kumar",
                "Cardiology",
                "Heart Specialist",
                "Monday, Wednesday, Friday",
                700
            ),
            (
                "Dr. Priya Sharma",
                "Dermatology",
                "Skin Specialist",
                "Tuesday, Thursday, Saturday",
                600
            ),
            (
                "Dr. Ravi Teja",
                "Neurology",
                "Neurologist",
                "Monday, Tuesday, Thursday",
                900
            ),
            (
                "Dr. Sneha Reddy",
                "General Medicine",
                "General Physician",
                "Monday to Saturday",
                500
            ),
            (
                "Dr. Kiran Rao",
                "Orthopedics",
                "Bone and Joint Specialist",
                "Wednesday, Friday, Saturday",
                750
            )
        ]

        cursor.executemany("""
            INSERT INTO doctors
            (name, department, specialization, available_days, fee)
            VALUES (?, ?, ?, ?, ?)
        """, doctors)

    conn.commit()
    conn.close()


create_database()


# --------------------------------------------------
# Database Helper Functions
# --------------------------------------------------

def get_doctors():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, department, specialization,
               available_days, fee
        FROM doctors
    """)

    doctors = cursor.fetchall()
    conn.close()

    return doctors


def save_appointment(
    patient_name,
    phone,
    doctor_name,
    department,
    appointment_date,
    appointment_time
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO appointments
        (
            patient_name,
            phone,
            doctor_name,
            department,
            appointment_date,
            appointment_time
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        patient_name,
        phone,
        doctor_name,
        department,
        appointment_date,
        appointment_time
    ))

    conn.commit()
    appointment_id = cursor.lastrowid
    conn.close()

    return appointment_id


def get_appointments():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, patient_name, phone,
               doctor_name, department,
               appointment_date, appointment_time
        FROM appointments
        ORDER BY appointment_date, appointment_time
    """)

    appointments = cursor.fetchall()
    conn.close()

    return appointments


# --------------------------------------------------
# AI Assistant
# --------------------------------------------------

def ask_ai(user_question):

    doctors = get_doctors()

    doctor_information = ""

    for doctor in doctors:
        doctor_information += f"""
Doctor: {doctor[0]}
Department: {doctor[1]}
Specialization: {doctor[2]}
Available Days: {doctor[3]}
Consultation Fee: ₹{doctor[4]}
-------------------------
"""

    system_prompt = f"""
You are an AI Hospital Query and Appointment Assistant.

Your job is to help patients with general hospital information.

Hospital Information:
- Hospital Name: AI Care Hospital
- Emergency Service: Available 24/7
- OPD Timing: 9:00 AM to 6:00 PM
- Emergency Department: Open 24/7
- Contact: 1800-123-4567

Available Doctors:
{doctor_information}

Instructions:
1. Answer questions clearly and politely.
2. Use only the hospital information provided above.
3. Do not diagnose diseases.
4. Do not prescribe medicines.
5. For medical emergencies, advise the patient to contact emergency services
   or visit the emergency department immediately.
6. If the patient wants an appointment, tell them to use the
   Appointment Booking section.
7. Do not invent doctors, fees, timings, or hospital services.
"""

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_question
                }
            ]
        )

        return response["message"]["content"]

    except Exception as e:
        return (
            "⚠️ AI service is not available.\n\n"
            "Please make sure Ollama is installed and running, "
            f"and the model '{OLLAMA_MODEL}' is available."
        )


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("🏥 AI-Based Hospital Query and Appointment Assistant")

st.write(
    "Ask hospital-related questions and book doctor appointments "
    "using an AI-powered assistant."
)

st.divider()


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

st.sidebar.title("🏥 Hospital Menu")

menu = st.sidebar.radio(
    "Select an option:",
    [
        "🤖 AI Hospital Assistant",
        "👨‍⚕️ Doctors",
        "📅 Book Appointment",
        "📋 Appointments"
    ]
)


# --------------------------------------------------
# AI Assistant
# --------------------------------------------------

if menu == "🤖 AI Hospital Assistant":

    st.header("🤖 AI Hospital Assistant")

    st.info(
        "You can ask questions such as:\n"
        "- What are the hospital timings?\n"
        "- Which doctors are available?\n"
        "- I need a cardiologist.\n"
        "- What is the consultation fee?\n"
        "- Is emergency service available?"
    )

    question = st.text_area(
        "Enter your question:",
        placeholder="Ask your hospital-related question..."
    )

    if st.button("Ask AI", type="primary"):

        if question.strip():

            with st.spinner("AI is thinking..."):

                answer = ask_ai(question)

            st.subheader("AI Response")
            st.write(answer)

        else:
            st.warning("Please enter a question.")


# --------------------------------------------------
# Doctors
# --------------------------------------------------

elif menu == "👨‍⚕️ Doctors":

    st.header("👨‍⚕️ Available Doctors")

    doctors = get_doctors()

    for doctor in doctors:

        with st.container(border=True):

            st.subheader(doctor[0])

            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Department:** {doctor[1]}")
                st.write(f"**Specialization:** {doctor[2]}")

            with col2:
                st.write(f"**Available:** {doctor[3]}")
                st.write(f"**Consultation Fee:** ₹{doctor[4]}")


# --------------------------------------------------
# Appointment Booking
# --------------------------------------------------

elif menu == "📅 Book Appointment":

    st.header("📅 Book Doctor Appointment")

    doctors = get_doctors()

    doctor_names = [doctor[0] for doctor in doctors]

    selected_doctor = st.selectbox(
        "Select Doctor",
        doctor_names
    )

    selected_doctor_data = None

    for doctor in doctors:
        if doctor[0] == selected_doctor:
            selected_doctor_data = doctor
            break

    patient_name = st.text_input(
        "Patient Name"
    )

    phone = st.text_input(
        "Phone Number"
    )

    appointment_date = st.date_input(
        "Appointment Date",
        min_value=date.today()
    )

    appointment_time = st.selectbox(
        "Appointment Time",
        [
            "09:00 AM",
            "10:00 AM",
            "11:00 AM",
            "12:00 PM",
            "02:00 PM",
            "03:00 PM",
            "04:00 PM",
            "05:00 PM"
        ]
    )

    if selected_doctor_data:

        st.info(
            f"Department: {selected_doctor_data[1]} | "
            f"Specialization: {selected_doctor_data[2]} | "
            f"Fee: ₹{selected_doctor_data[4]}"
        )

    if st.button("Book Appointment", type="primary"):

        if not patient_name.strip():

            st.error("Please enter patient name.")

        elif not phone.strip():

            st.error("Please enter phone number.")

        elif len(phone) < 10:

            st.error("Please enter a valid phone number.")

        else:

            appointment_id = save_appointment(
                patient_name,
                phone,
                selected_doctor_data[0],
                selected_doctor_data[1],
                str(appointment_date),
                appointment_time
            )

            st.success(
                f"✅ Appointment booked successfully! "
                f"Appointment ID: {appointment_id}"
            )

            st.balloons()


# --------------------------------------------------
# Appointments
# --------------------------------------------------

elif menu == "📋 Appointments":

    st.header("📋 Appointment Records")

    appointments = get_appointments()

    if appointments:

        for appointment in appointments:

            with st.container(border=True):

                st.write(
                    f"**Appointment ID:** {appointment[0]}"
                )

                st.write(
                    f"**Patient:** {appointment[1]}"
                )

                st.write(
                    f"**Phone:** {appointment[2]}"
                )

                st.write(
                    f"**Doctor:** {appointment[3]}"
                )

                st.write(
                    f"**Department:** {appointment[4]}"
                )

                st.write(
                    f"**Date:** {appointment[5]}"
                )

                st.write(
                    f"**Time:** {appointment[6]}"
                )

    else:

        st.info("No appointments have been booked yet.")


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.divider()

st.caption(
    "🏥 AI-Based Hospital Query and Appointment Assistant | "
    "For general hospital information only."
)