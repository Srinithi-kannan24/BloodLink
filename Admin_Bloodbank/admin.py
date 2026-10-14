from datetime import date
import uuid

from flask import Blueprint, render_template, redirect, session, url_for, request, jsonify

from config import get_db_connection

admin = Blueprint("admin", __name__)

@admin.route("/admin")
def admin_dashboard():
    if session.get("db_role") != "Admin":
        return redirect(url_for("auth.login"))
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id,full_name,email,role,phone,status FROM users ORDER BY created_at DESC,user_id")
        users = cursor.fetchall()
        total_users = len(users)
        active_users = sum(user["status"] == "Active" for user in users)
        current_admin = next((user for user in users if user["user_id"] == session.get("user_id")), None)
        counts = {}
        count_queries = {
            "total_banks": "SELECT COUNT(*) n FROM blood_banks",
            "total_hospitals": "SELECT COUNT(*) n FROM hospitals",
            "total_donors": "SELECT COUNT(*) n FROM donors",
            "pending_requests": "SELECT COUNT(*) n FROM blood_requests WHERE status='Pending'",
            "pending_verifications": "SELECT COUNT(*) n FROM users WHERE status='Pending Verification'",
            "new_users_today": "SELECT COUNT(*) n FROM users WHERE created_at=CURDATE()",
            "expired_units": "SELECT COUNT(*) n FROM blood_units WHERE status='Available' AND expiry_date<CURDATE()",
            "total_donations": "SELECT COUNT(*) n FROM donations WHERE status='Completed'",
            "total_allocations": "SELECT COUNT(*) n FROM allocation",
            "total_requests": "SELECT COUNT(*) n FROM blood_requests",
        }
        for key, query in count_queries.items():
            cursor.execute(query)
            counts[key] = cursor.fetchone()["n"]
        cursor.execute("SELECT COALESCE(SUM(units),0) n FROM blood_units WHERE status='Available' AND expiry_date>=CURDATE()")
        counts["current_units"] = cursor.fetchone()["n"]

        cursor.execute("""SELECT b.BankID,b.BankName,b.District,b.BankType,
                          (SELECT COUNT(*) FROM users u WHERE u.blood_bank_id=b.BankID) staff_count,
                          (SELECT COALESCE(SUM(bu.units),0) FROM blood_units bu WHERE bu.blood_bank_id=b.BankID
                           AND bu.status='Available' AND bu.expiry_date>=CURDATE()) available_units
                          FROM blood_banks b ORDER BY b.BankName""")
        bank_rows = cursor.fetchall()
        cursor.execute("""SELECT h.hospital_id,h.hospital_name,h.district,
                          COUNT(DISTINCT u.user_id) staff_count,
                          COUNT(DISTINCT br.request_id) request_count,
                          COUNT(DISTINCT CASE WHEN br.status='Pending' THEN br.request_id END) pending_count
                          FROM hospitals h LEFT JOIN users u ON u.hospital_id=h.hospital_id
                          LEFT JOIN blood_requests br ON br.hospital_id=h.hospital_id
                          GROUP BY h.hospital_id,h.hospital_name,h.district ORDER BY h.hospital_name""")
        hospital_rows = cursor.fetchall()

        cursor.execute("""SELECT event_title,event_description,event_date FROM (
                          SELECT 'Allocation completed' event_title,
                          CONCAT('Request ',a.request_id,' allocated by ',b.BankName) event_description,
                          a.allocation_date event_date FROM allocation a JOIN blood_banks b ON b.BankID=a.blood_bank_id
                          UNION ALL
                          SELECT 'Hospital request',CONCAT(h.hospital_name,' requested ',br.units_required,' units of ',br.blood_group),br.request_date
                          FROM blood_requests br JOIN hospitals h ON h.hospital_id=br.hospital_id
                          UNION ALL
                          SELECT 'User registered',CONCAT(u.full_name,' joined as ',u.role),u.created_at FROM users u
                          UNION ALL
                          SELECT 'Donation appointment',CONCAT(usr.full_name,' booked at ',b.BankName),a.appointment_date
                          FROM appointments a JOIN donors d ON d.donor_id=a.donor_id JOIN users usr ON usr.user_id=d.user_id
                          JOIN blood_banks b ON b.BankID=a.blood_bank_id
                          ) events ORDER BY event_date DESC LIMIT 10""")
        activity = cursor.fetchall()

        cursor.execute("""SELECT bg.blood_group,
                          (SELECT COUNT(*) FROM donations dn JOIN donors d ON d.donor_id=dn.donor_id WHERE d.blood_group=bg.blood_group AND dn.status='Completed') donations,
                          (SELECT COUNT(*) FROM blood_requests br WHERE br.blood_group=bg.blood_group) requests,
                          (SELECT COUNT(*) FROM allocation a JOIN blood_units bu ON bu.unit_id=a.unit_id WHERE bu.blood_group=bg.blood_group) allocations,
                          (SELECT COALESCE(SUM(bu.units),0) FROM blood_units bu WHERE bu.blood_group=bg.blood_group AND bu.status='Available' AND bu.expiry_date>=CURDATE()) current_units
                          FROM (SELECT 'A+' blood_group UNION ALL SELECT 'A-' UNION ALL SELECT 'B+' UNION ALL SELECT 'B-' UNION ALL SELECT 'AB+' UNION ALL SELECT 'AB-' UNION ALL SELECT 'O+' UNION ALL SELECT 'O-') bg
                          ORDER BY FIELD(bg.blood_group,'A+','A-','B+','B-','O+','O-','AB+','AB-')""")
        blood_group_activity = cursor.fetchall()
        cursor.execute("SELECT hospital_id,hospital_name FROM hospitals ORDER BY hospital_name")
        hospitals = cursor.fetchall()
        cursor.execute("SELECT BankID,BankName FROM blood_banks ORDER BY BankName")
        blood_banks = cursor.fetchall()
        return render_template("admin_dashboard.html", users=users, hospitals=hospitals, blood_banks=blood_banks,
                               total_users=total_users, active_users=active_users, current_admin=current_admin,
                               bank_rows=bank_rows, hospital_rows=hospital_rows, activity=activity,
                               blood_group_activity=blood_group_activity, **counts)
    finally:
        cursor.close()
        db.close()


@admin.route("/admin/users/<user_id>/status", methods=["POST"])
def update_user_status(user_id):
    if session.get("db_role") != "Admin":
        return jsonify({"success": False, "message": "Admin access required."}), 403
    status = request.form.get("status")
    if status not in {"Active", "Inactive"}:
        return jsonify({"success": False, "message": "Invalid account status."}), 400
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE users SET status=%s WHERE user_id=%s", (status, user_id))
        if cursor.rowcount != 1:
            db.rollback()
            return jsonify({"success": False, "message": "User not found."}), 404
        db.commit()
        return jsonify({"success": True, "status": status})
    except Exception as exc:
        db.rollback()
        return jsonify({"success": False, "message": str(exc)}), 500
    finally:
        cursor.close()
        db.close()


@admin.route("/admin/users", methods=["POST"])
def create_user():
    if session.get("db_role") != "Admin":
        return jsonify({"success": False, "message": "Admin access required."}), 403
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "")
    phone = request.form.get("phone", "").strip()
    if not full_name or not email or not password or role not in {"Donor", "HospitalStaff", "BloodBankStaff", "Admin"}:
        return jsonify({"success": False, "message": "Complete all required user fields."}), 400
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        hospital_id = request.form.get("hospital_id") or None
        blood_bank_id = request.form.get("blood_bank_id") or None
        if role == "HospitalStaff" and not hospital_id:
            return jsonify({"success": False, "message": "Select the staff member's hospital."}), 400
        if role == "BloodBankStaff" and not blood_bank_id:
            return jsonify({"success": False, "message": "Select the staff member's blood bank."}), 400
        if role != "HospitalStaff":
            hospital_id = None
        if role != "BloodBankStaff":
            blood_bank_id = None
        cursor.execute("SELECT user_id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "Email is already registered."}), 409
        user_id = "USR" + uuid.uuid4().hex[:17].upper()
        cursor.execute("""INSERT INTO users
                       (user_id,full_name,email,password,role,phone,status,created_at,hospital_id,blood_bank_id)
                       VALUES (%s,%s,%s,%s,%s,%s,'Active',%s,%s,%s)""",
                       (user_id,full_name,email,password,role,phone,date.today(),hospital_id,blood_bank_id))
        if role == "Donor":
            donor_values = [request.form.get(key, "").strip() for key in ("blood_group", "gender", "date_of_birth", "weight_kg", "city", "district")]
            blood_group, gender, dob, weight, city, district = donor_values
            if blood_group not in {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"} or gender not in {"Male", "Female"} or not dob or not city or not district:
                db.rollback()
                return jsonify({"success": False, "message": "Complete the donor profile with valid blood group, gender, birth date, city, and district."}), 400
            try:
                weight = float(weight)
                if weight <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                db.rollback()
                return jsonify({"success": False, "message": "Donor weight must be a positive number."}), 400
            donor_id = "DNR" + uuid.uuid4().hex[:17].upper()
            cursor.execute("""INSERT INTO donors
                           (donor_id,user_id,blood_group,gender,date_of_birth,weight_kg,city,district,last_donation_date,availability,eligibility)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NULL,'Available','Eligible')""",
                           (donor_id,user_id,blood_group,gender,dob,weight,city,district))
        db.commit()
        return jsonify({"success": True, "message": "User created."})
    except Exception as exc:
        db.rollback()
        return jsonify({"success": False, "message": str(exc)}), 500
    finally:
        cursor.close()
        db.close()


@admin.route("/admin/profile", methods=["POST"])
def update_admin_profile():
    if session.get("db_role") != "Admin":
        return jsonify({"success": False, "message": "Admin access required."}), 403
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    if not name or not email:
        return jsonify({"success": False, "message": "Name and email are required."}), 400
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE users SET full_name=%s,email=%s,phone=%s WHERE user_id=%s AND role='Admin'", (name,email,phone,session.get("user_id")))
        if cursor.rowcount != 1:
            db.rollback()
            return jsonify({"success": False, "message": "Admin profile not found."}), 404
        db.commit()
        session["name"] = name
        return jsonify({"success": True, "message": "Profile updated."})
    except Exception as exc:
        db.rollback()
        return jsonify({"success": False, "message": str(exc)}), 500
    finally:
        cursor.close()
        db.close()
