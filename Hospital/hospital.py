from datetime import date
import uuid

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from config import get_db_connection

hospital = Blueprint("hospital", __name__)


def _hospital_staff(cursor):
    cursor.execute("""SELECT u.user_id,u.full_name,u.email,u.phone,u.status,u.hospital_id,
                      h.hospital_name,h.district,h.phone AS hospital_phone
                      FROM users u LEFT JOIN hospitals h ON h.hospital_id=u.hospital_id
                      WHERE u.user_id=%s AND u.role='HospitalStaff'""", (session.get("user_id"),))
    return cursor.fetchone()


@hospital.route("/hospital")
def hospital_dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        staff = _hospital_staff(cursor)
        if not staff or not staff["hospital_id"]:
            return "Hospital staff profile is not linked to a hospital", 404
        hid = staff["hospital_id"]
        cursor.execute("SELECT COUNT(*) total_requests, SUM(status='Pending') pending_requests, SUM(status='Approved') approved_requests, SUM(status='Fulfilled') fulfilled_requests FROM blood_requests WHERE hospital_id=%s", (hid,))
        summary = cursor.fetchone()
        cursor.execute("SELECT * FROM blood_requests WHERE hospital_id=%s ORDER BY request_date DESC", (hid,))
        requests_list = cursor.fetchall()
        cursor.execute("""SELECT a.allocation_id,a.request_id,a.allocation_date,a.status,
                          br.blood_group,bu.units,bu.unit_id
                          FROM allocation a JOIN blood_requests br ON br.request_id=a.request_id
                          JOIN blood_units bu ON bu.unit_id=a.unit_id
                          WHERE br.hospital_id=%s ORDER BY a.allocation_date DESC""", (hid,))
        allocations_list = cursor.fetchall()
        summary["allocated_units"] = sum(row["units"] for row in allocations_list)
        summary["completed_allocations"] = len(allocations_list)
        cursor.execute("""SELECT COALESCE(SUM(bu.units),0) AS allocations_this_month
                          FROM allocation a JOIN blood_requests br ON br.request_id=a.request_id
                          JOIN blood_units bu ON bu.unit_id=a.unit_id
                          WHERE br.hospital_id=%s AND YEAR(a.allocation_date)=YEAR(CURDATE())
                          AND MONTH(a.allocation_date)=MONTH(CURDATE())""", (hid,))
        summary["allocations_this_month"] = cursor.fetchone()["allocations_this_month"]
        return render_template("hospital_dashboard.html", staff=staff, **summary,
                               requests_list=requests_list, allocations_list=allocations_list,
                               today=date.today())
    finally:
        cursor.close()
        db.close()


@hospital.route("/hospital/request", methods=["POST"])
def create_blood_request():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please login first."}), 401
    group = request.form.get("blood_group", "")
    urgency = request.form.get("urgency", "")
    required_date = request.form.get("required_date", "")
    try:
        units = int(request.form.get("units", ""))
    except ValueError:
        return jsonify({"success": False, "message": "Units must be a positive integer."}), 400
    if group not in {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"} or urgency not in {"Routine", "Urgent", "Emergency"} or units < 1 or not required_date:
        return jsonify({"success": False, "message": "Please provide valid request details."}), 400
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        staff = _hospital_staff(cursor)
        if not staff or not staff["hospital_id"]:
            return jsonify({"success": False, "message": "Hospital staff profile is not linked to a hospital."}), 403
        request_id = "REQ" + uuid.uuid4().hex[:10].upper()
        cursor.execute("""INSERT INTO blood_requests
                       (request_id,hospital_id,blood_group,units_required,request_date,required_date,urgency,status)
                       VALUES (%s,%s,%s,%s,CURDATE(),%s,%s,'Pending')""",
                       (request_id, staff["hospital_id"], group, units, required_date, urgency))
        db.commit()
        return jsonify({"success": True, "message": "Blood request submitted.", "request_id": request_id})
    except Exception as exc:
        db.rollback()
        return jsonify({"success": False, "message": str(exc)}), 500
    finally:
        cursor.close()
        db.close()


@hospital.route("/hospital/profile", methods=["POST"])
def update_hospital_profile():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please login first."}), 401
    name, email, phone = (request.form.get(k, "").strip() for k in ("name", "email", "phone"))
    if not name or not email:
        return jsonify({"success": False, "message": "Name and email are required."}), 400
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE users SET full_name=%s,email=%s,phone=%s WHERE user_id=%s AND role='HospitalStaff'", (name, email, phone, session["user_id"]))
        if cursor.rowcount != 1:
            db.rollback()
            return jsonify({"success": False, "message": "Hospital staff profile not found."}), 404
        db.commit()
        session["name"] = name
        return jsonify({"success": True, "message": "Profile updated."})
    except Exception as exc:
        db.rollback()
        return jsonify({"success": False, "message": str(exc)}), 500
    finally:
        cursor.close()
        db.close()
