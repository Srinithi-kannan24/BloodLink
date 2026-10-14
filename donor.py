from flask import Blueprint, render_template, session, redirect, url_for, request
from config import get_db_connection
from datetime import date
donor_bp = Blueprint("donor", __name__)
import uuid

@donor_bp.route("/donor_dashboard")
def donor_dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # -----------------------------------------
        # Get donor profile
        # -----------------------------------------

        cursor.execute(
            """
            SELECT
                u.user_id,
                u.full_name,
                u.email,
                u.phone,
                d.donor_id,
                d.blood_group,
                d.gender,
                d.date_of_birth,
                d.weight_kg,
                d.city,
                d.district,
                d.last_donation_date,
                d.availability,
                d.eligibility
            FROM users u
            INNER JOIN donors d
                ON u.user_id = d.user_id
            WHERE u.user_id = %s
            """,
            (user_id,)
        )

        donor = cursor.fetchone()

        if not donor:
            return "Donor profile not found", 404

        donor_id = donor["donor_id"]

        # -----------------------------------------
        # Total donations
        # -----------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS total_donations
            FROM donations
            WHERE donor_id = %s
            AND status = 'Completed'
            """,
            (donor_id,)
        )

        result = cursor.fetchone()
        total_donations = result["total_donations"] or 0

        # -----------------------------------------
        # Lives impacted
        # -----------------------------------------

        lives_impacted = total_donations

        # -----------------------------------------
        # Next appointment
        # -----------------------------------------

        cursor.execute(
            """
            SELECT
                appointment_id,
                appointment_date,
                time_slot,
                status,
                blood_bank_id
            FROM appointments
            WHERE donor_id = %s
            AND appointment_date >= CURDATE()
            AND status NOT IN ('Cancelled', 'Completed')
            ORDER BY appointment_date ASC, time_slot ASC
            LIMIT 1
            """,
            (donor_id,)
        )

        next_appointment = cursor.fetchone()

        # -----------------------------------------
        # Recent donations
        # -----------------------------------------

        cursor.execute(
            """
            SELECT
                dn.donation_id,
                dn.donation_date,
                dn.units,
                dn.status,
                d.blood_group,
                b.BankName,
                b.District
            FROM donations dn
            INNER JOIN donors d
                ON dn.donor_id = d.donor_id
            LEFT JOIN blood_banks b
                ON dn.blood_bank_id = b.BankID
            WHERE dn.donor_id = %s
            ORDER BY dn.donation_date DESC
            LIMIT 5
            """,
            (donor_id,)
        )

        recent_donations = cursor.fetchall()

        # -----------------------------------------
        # Upcoming appointments
        # -----------------------------------------

        cursor.execute(
            """
            SELECT
                a.appointment_id,
                a.appointment_date,
                a.time_slot,
                a.status,
                b.BankName,
                b.District
            FROM appointments a
            LEFT JOIN blood_banks b
                ON a.blood_bank_id = b.BankID
            WHERE a.donor_id = %s
            AND a.appointment_date >= CURDATE()
            ORDER BY a.appointment_date ASC, a.time_slot ASC
            LIMIT 5
            """,
            (donor_id,)
        )

        upcoming_appointments = cursor.fetchall()
        cursor.execute(
                """
                SELECT
                 BankID,
                 BankName,
                 District
                FROM blood_banks
                ORDER BY BankName
                """,
                )

        blood_banks = cursor.fetchall()

        return render_template(
            "donor_dashboard.html",
            donor=donor,
            total_donations=total_donations,
            lives_impacted=lives_impacted,
            next_appointment=next_appointment,
            recent_donations=recent_donations,
            upcoming_appointments=upcoming_appointments,
            blood_banks=blood_banks,
            today=date.today()
        )

    finally:
        cursor.close()
        db.close()

@donor_bp.route("/donation_history")
def donation_history():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT donor_id
            FROM donors
            WHERE user_id = %s
            """,
            (user_id,)
        )

        donor = cursor.fetchone()

        if not donor:
            return "Donor profile not found", 404

        donor_id = donor["donor_id"]

        cursor.execute(
            """
            SELECT
                dn.donation_id,
                dn.donation_date,
                dn.units,
                dn.status,
                d.blood_group,
                b.BankName,
                b.District
            FROM donations dn
            INNER JOIN donors d
                ON dn.donor_id = d.donor_id
            LEFT JOIN blood_banks b
                ON dn.blood_bank_id = b.BankID
            WHERE dn.donor_id = %s
            ORDER BY dn.donation_date DESC
            """,
            (donor_id,)
        )

        donations = cursor.fetchall()

        return render_template(
            "donation_history.html",
            donations=donations
        )

    finally:
        cursor.close()
        db.close()
@donor_bp.route("/appointments")
def appointments():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT donor_id
            FROM donors
            WHERE user_id = %s
            """,
            (user_id,)
        )

        donor = cursor.fetchone()

        if not donor:
            return "Donor profile not found", 404

        donor_id = donor["donor_id"]

        cursor.execute(
            """
            SELECT
                a.appointment_id,
                a.appointment_date,
                a.time_slot,
                a.status,
                b.BankName,
                b.District
            FROM appointments a
            LEFT JOIN blood_banks b
                ON a.blood_bank_id = b.BankID
            WHERE a.donor_id = %s
            ORDER BY a.appointment_date DESC, a.time_slot DESC
            """,
            (donor_id,)
        )

        appointments_list = cursor.fetchall()

        return render_template(
            "appointments.html",
            appointments=appointments_list
        )

    finally:
        cursor.close()
        db.close()
@donor_bp.route("/book_appointment", methods=["POST"])
def book_appointment():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    blood_bank_id = request.form.get("blood_bank_id")
    appointment_date = request.form.get("appointment_date")
    time_slot = request.form.get("time_slot")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT donor_id
            FROM donors
            WHERE user_id = %s
            """,
            (user_id,)
        )

        donor = cursor.fetchone()

        if not donor:
            return "Donor profile not found", 404

        donor_id = donor["donor_id"]

        cursor.execute(
            """
            SELECT appointment_id
            FROM appointments
            WHERE donor_id = %s
            AND appointment_date = %s
            AND time_slot = %s
            AND status NOT IN ('Cancelled', 'Completed')
            """,
            (
                donor_id,
                appointment_date,
                time_slot
            )
        )

        existing = cursor.fetchone()

        if existing:
            return "You already have an appointment for this date and time slot."

        appointment_id = "APT" + uuid.uuid4().hex[:17]

        cursor.execute(
            """
            INSERT INTO appointments
            (
                appointment_id,
                donor_id,
                blood_bank_id,
                appointment_date,
                time_slot,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                appointment_id,
                donor_id,
                blood_bank_id,
                appointment_date,
                time_slot,
                "Scheduled"
            )
        )

        db.commit()

        return redirect(url_for("donor.appointments"))

    except Exception:
        db.rollback()
        raise

    finally:
        cursor.close()
        db.close()
# ==============================
# Update Donor Availability
# ==============================

@donor_bp.route("/update_availability", methods=["POST"])
def update_availability():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    availability = request.form.get("availability", "").strip()

    print("================================")
    print("USER ID:", user_id)
    print("AVAILABILITY:", repr(availability))
    print("================================")

    if availability not in ["Available", "Unavailable"]:
        print("INVALID AVAILABILITY VALUE")
        return redirect(url_for("donor.donor_dashboard"))

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("SELECT DATABASE()")
        print("DATABASE:", cursor.fetchone())

        cursor.execute(
            """
            UPDATE donors
            SET availability = %s
            WHERE user_id = %s
            """,
            (availability, user_id)
        )

        print("ROWS UPDATED:", cursor.rowcount)

        db.commit()

        return redirect(url_for("donor.donor_dashboard"))

    except Exception as e:

        print("UPDATE ERROR:", e)

        db.rollback()
        raise

    finally:

        cursor.close()
        db.close()
# ==============================
# Change Password
# ==============================

@donor_bp.route("/change_password", methods=["POST"])
def change_password():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if new_password != confirm_password:
        return redirect(url_for("donor.donor_dashboard"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT password
            FROM users
            WHERE user_id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:
            return redirect(url_for("auth.login"))

        if user["password"] != current_password:
            return redirect(url_for("donor.donor_dashboard"))

        cursor.execute(
            """
            UPDATE users
            SET password = %s
            WHERE user_id = %s
            """,
            (new_password, user_id)
        )

        db.commit()

        return redirect(url_for("donor.donor_dashboard"))

    except Exception:
        db.rollback()
        raise

    finally:
        cursor.close()
        db.close()