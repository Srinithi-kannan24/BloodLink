from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from config import get_db_connection
from datetime import date
import uuid


bloodbank = Blueprint("bloodbank", __name__)


# =========================================================
# HELPER: GET LOGGED-IN BLOOD BANK STAFF
# =========================================================

def get_staff_and_bank(cursor):

    user_id = session.get("user_id")

    if not user_id:
        return None

    cursor.execute(
        """
        SELECT
            u.user_id,
            u.full_name,
            u.email,
            u.phone,
            u.role,
            u.status,
            u.blood_bank_id,
            b.BankID,
            b.BankName,
            b.District
        FROM users u
        LEFT JOIN blood_banks b
            ON u.blood_bank_id = b.BankID
        WHERE u.user_id = %s
        AND u.role = 'BloodBankStaff'
        """,
        (user_id,)
    )

    return cursor.fetchone()


# =========================================================
# BLOOD BANK DASHBOARD
# =========================================================

@bloodbank.route("/bloodbank")
def bloodbank_dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:

        # -------------------------------------------------
        # STAFF + BLOOD BANK
        # -------------------------------------------------

        staff = get_staff_and_bank(cursor)

        if not staff:
            return "Blood Bank staff profile not found", 404

        blood_bank_id = staff["blood_bank_id"]

        if not blood_bank_id:
            return "No blood bank is assigned to this staff member", 400


        # =================================================
        # DASHBOARD SUMMARY
        # =================================================

        # Total quantity of blood units
        cursor.execute(
            """
            SELECT COALESCE(SUM(units), 0) AS total_units
            FROM blood_units
            WHERE blood_bank_id = %s
            """,
            (blood_bank_id,)
        )

        total_units = cursor.fetchone()["total_units"]


        # Available quantity
        cursor.execute(
            """
            SELECT COALESCE(SUM(units), 0) AS available_units
            FROM blood_units
            WHERE blood_bank_id = %s
            AND status = 'Available'
            AND expiry_date >= CURDATE()
            """,
            (blood_bank_id,)
        )

        available_units = cursor.fetchone()["available_units"]


        # Pending requests
        cursor.execute(
            """
            SELECT COUNT(*) AS pending_requests
            FROM blood_requests
            WHERE status = 'Pending'
            """
        )

        pending_requests = cursor.fetchone()["pending_requests"]


        # Today's appointments
        cursor.execute(
            """
            SELECT COUNT(*) AS today_appointments
            FROM appointments
            WHERE blood_bank_id = %s
            AND appointment_date = CURDATE()
            AND status NOT IN ('Cancelled', 'Completed')
            """,
            (blood_bank_id,)
        )

        today_appointments = cursor.fetchone()["today_appointments"]


        # =================================================
        # RECENT DONATIONS
        # =================================================

        cursor.execute(
            """
            SELECT
                dn.donation_id,
                dn.donor_id,
                u.full_name,
                d.blood_group,
                dn.donation_date,
                dn.units,
                dn.status
            FROM donations dn
            INNER JOIN donors d
                ON dn.donor_id = d.donor_id
            INNER JOIN users u
                ON d.user_id = u.user_id
            WHERE dn.blood_bank_id = %s
            ORDER BY dn.donation_date DESC
            LIMIT 5
            """,
            (blood_bank_id,)
        )

        recent_donations = cursor.fetchall()


        # =================================================
        # INVENTORY SUMMARY
        # =================================================

        cursor.execute(
            """
            SELECT
                COALESCE(SUM(units), 0) AS inventory_total_units,
                COALESCE(
                    SUM(
                        CASE
                            WHEN status = 'Available'
                            AND expiry_date >= CURDATE()
                            THEN units
                            ELSE 0
                        END
                    ), 0
                ) AS inventory_available_units
            FROM blood_units
            WHERE blood_bank_id = %s
            """,
            (blood_bank_id,)
        )

        inventory_summary = cursor.fetchone()

        inventory_total_units = inventory_summary["inventory_total_units"]
        inventory_available_units = inventory_summary["inventory_available_units"]


        # =================================================
        # INVENTORY BY BLOOD GROUP
        # =================================================

        cursor.execute(
            """
            SELECT
                bg.blood_group,

                COALESCE(
                    SUM(
                        CASE
                            WHEN bu.blood_group = bg.blood_group
                            THEN bu.units
                            ELSE 0
                        END
                    ), 0
                ) AS total_units,

                COALESCE(
                    SUM(
                        CASE
                            WHEN bu.blood_group = bg.blood_group
                            AND bu.status = 'Available'
                            AND bu.expiry_date >= CURDATE()
                            THEN bu.units
                            ELSE 0
                        END
                    ), 0
                ) AS available_units,

                COALESCE(
                    SUM(
                        CASE
                            WHEN bu.blood_group = bg.blood_group
                            AND bu.status = 'Available'
                            AND bu.expiry_date >= CURDATE()
                            AND bu.expiry_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)
                            THEN bu.units
                            ELSE 0
                        END
                    ), 0
                ) AS expiring_soon

            FROM
            (
                SELECT 'A+' AS blood_group
                UNION ALL SELECT 'A-'
                UNION ALL SELECT 'B+'
                UNION ALL SELECT 'B-'
                UNION ALL SELECT 'O+'
                UNION ALL SELECT 'O-'
                UNION ALL SELECT 'AB+'
                UNION ALL SELECT 'AB-'
            ) bg

            LEFT JOIN blood_units bu
                ON bu.blood_group = bg.blood_group
                AND bu.blood_bank_id = %s

            GROUP BY bg.blood_group

            ORDER BY
                FIELD(
                    bg.blood_group,
                    'A+','A-','B+','B-',
                    'O+','O-','AB+','AB-'
                )
            """,
            (blood_bank_id,)
        )

        inventory_data = cursor.fetchall()


        # -------------------------------------------------
        # LOW STOCK
        #
        # Business rule used here:
        # Available quantity:
        # 0       -> Critical
        # 1-4     -> Low Stock
        # 5+      -> Available
        # -------------------------------------------------

        inventory_low_stock_units = sum(
            1
            for item in inventory_data
            if item["available_units"] > 0
            and item["available_units"] < 5
        )


        # =================================================
        # TOTAL UNITS EXPIRING WITHIN 7 DAYS
        # =================================================

        cursor.execute(
            """
            SELECT COALESCE(SUM(units), 0) AS expiring_soon
            FROM blood_units
            WHERE blood_bank_id = %s
            AND status = 'Available'
            AND expiry_date >= CURDATE()
            AND expiry_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)
            """,
            (blood_bank_id,)
        )

        inventory_expiring_soon = cursor.fetchone()["expiring_soon"]


        # Add status to inventory rows
        for item in inventory_data:

            if item["available_units"] == 0:
                item["status"] = "Critical"

            elif item["available_units"] < 5:
                item["status"] = "Low Stock"

            else:
                item["status"] = "Available"

            # Your database does not have a Reserved status.
            # Therefore we do not invent one.
            item["reserved_units"] = 0


        # =================================================
        # TODAY'S APPOINTMENTS
        # =================================================

        cursor.execute(
            """
            SELECT
                a.appointment_id,
                a.appointment_date,
                a.time_slot,
                a.status,
                d.donor_id,
                d.blood_group,
                u.full_name
            FROM appointments a

            INNER JOIN donors d
                ON a.donor_id = d.donor_id

            INNER JOIN users u
                ON d.user_id = u.user_id

            WHERE a.blood_bank_id = %s
            AND a.appointment_date = CURDATE()

            ORDER BY a.time_slot ASC
            """,
            (blood_bank_id,)
        )

        today_appointments_list = cursor.fetchall()


        # =================================================
        # ALL DONATIONS
        # =================================================

        cursor.execute(
            """
            SELECT
                dn.donation_id,
                dn.donor_id,
                u.full_name,
                d.blood_group,
                dn.units,
                dn.donation_date,
                dn.status
            FROM donations dn

            INNER JOIN donors d
                ON dn.donor_id = d.donor_id

            INNER JOIN users u
                ON d.user_id = u.user_id

            WHERE dn.blood_bank_id = %s

            ORDER BY dn.donation_date DESC
            """,
            (blood_bank_id,)
        )

        donations_list = cursor.fetchall()


        # =================================================
        # HOSPITAL REQUESTS
        #
        # blood_requests does NOT contain blood_bank_id.
        # Therefore requests are shown globally.
        # =================================================

        cursor.execute(
            """
            SELECT br.request_id, br.hospital_id, br.blood_group, br.units_required,
                   br.request_date, br.required_date, br.urgency, br.status, h.hospital_name
            FROM blood_requests br
            INNER JOIN hospitals h ON h.hospital_id = br.hospital_id
            WHERE br.status IN ('Pending', 'Approved')
            ORDER BY
                CASE
                    WHEN br.urgency = 'Emergency' THEN 1
                    WHEN br.urgency = 'Urgent' THEN 2
                    ELSE 3
                END,
                br.request_date DESC
            """
        )

        requests_list = cursor.fetchall()


        # =================================================
        # EMERGENCY REQUESTS
        # =================================================

        cursor.execute(
            """
            SELECT
                br.request_id,
                br.hospital_id,
                br.blood_group,
                br.units_required,
                br.request_date,
                br.required_date,
                br.urgency,
                br.status,
                h.hospital_name
            FROM blood_requests br
            INNER JOIN hospitals h ON h.hospital_id = br.hospital_id
            WHERE br.status IN ('Pending', 'Approved')
            AND urgency IN ('Urgent', 'Emergency')
            ORDER BY request_date DESC
            LIMIT 5
            """
        )

        emergency_requests = cursor.fetchall()


        # =================================================
        # ALLOCATIONS
        # =================================================

        cursor.execute(
            """
            SELECT
                a.allocation_id,
                a.request_id,
                a.unit_id,
                a.blood_bank_id,
                a.allocation_date,
                a.status,
                br.hospital_id,
                h.hospital_name,
                br.blood_group,
                bu.units
            FROM allocation a

            INNER JOIN blood_requests br
                ON a.request_id = br.request_id

            INNER JOIN blood_units bu
                ON a.unit_id = bu.unit_id
            INNER JOIN hospitals h ON h.hospital_id = br.hospital_id

            WHERE a.blood_bank_id = %s

            ORDER BY a.allocation_date DESC
            """,
            (blood_bank_id,)
        )

        allocations_list = cursor.fetchall()

        cursor.execute("""SELECT donation_id, donation_date, units FROM donations d
                       WHERE blood_bank_id = %s AND status = 'Completed'
                       AND NOT EXISTS (SELECT 1 FROM blood_units bu WHERE bu.donation_id = d.donation_id)
                       ORDER BY donation_date DESC""", (blood_bank_id,))
        eligible_donations = cursor.fetchall()

        cursor.execute("""SELECT unit_id,blood_group,units,expiry_date FROM blood_units
                       WHERE blood_bank_id=%s AND status='Available' AND expiry_date>=CURDATE()
                       ORDER BY expiry_date""", (blood_bank_id,))
        allocatable_units = cursor.fetchall()


        # =================================================
        # RENDER
        # =================================================

        return render_template(
            "bloodbank_dashboard.html",

            staff=staff,

            total_units=total_units,
            available_units=available_units,
            pending_requests=pending_requests,
            today_appointments=today_appointments,

            recent_donations=recent_donations,

            inventory_total_units=inventory_total_units,
            inventory_available_units=inventory_available_units,
            inventory_low_stock_units=inventory_low_stock_units,
            inventory_expiring_soon=inventory_expiring_soon,
            inventory_data=inventory_data,

            today_appointments_list=today_appointments_list,

            donations_list=donations_list,

            requests_list=requests_list,
            emergency_requests=emergency_requests,

            allocations_list=allocations_list,
            eligible_donations=eligible_donations,
            allocatable_units=allocatable_units,

            today=date.today()
        )

    finally:

        cursor.close()
        db.close()


# =========================================================
# ADD BLOOD UNIT
# =========================================================

@bloodbank.route("/bloodbank/add-unit", methods=["POST"])
def add_blood_unit():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    blood_group = request.form.get("blood_group")
    units = request.form.get("units")
    expiry_date = request.form.get("expiry_date")

    if blood_group not in {'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'} or not units or not expiry_date:
        return jsonify({
            "success": False,
            "message": "Please fill all fields."
        }), 400

    try:
        units = int(units)
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Units must be a number."
        }), 400

    if units <= 0:
        return jsonify({
            "success": False,
            "message": "Units must be greater than zero."
        }), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:

        staff = get_staff_and_bank(cursor)

        if not staff:
            return jsonify({
                "success": False,
                "message": "Blood Bank staff profile not found."
            }), 404

        blood_bank_id = staff["blood_bank_id"]

        if not blood_bank_id:
            return jsonify({
                "success": False,
                "message": "No blood bank assigned."
            }), 400


        # -------------------------------------------------
        # Generate Unit ID
        # -------------------------------------------------

        unit_id = "UNIT" + uuid.uuid4().hex[:16]


        # -------------------------------------------------
        # Donation ID is required by your blood_units table.
        #
        # Since the dashboard's Add Blood Unit form is only
        # adding inventory and is NOT recording a donor
        # donation, we do not insert a fake donation.
        #
        # Therefore this action should only be used when
        # a valid donation_id is supplied.
        # -------------------------------------------------

        donation_id = request.form.get("donation_id")

        if not donation_id:
            return jsonify({
                "success": False,
                "message": "A valid donation ID is required to create a blood unit."
            }), 400


        # -------------------------------------------------
        # Verify donation belongs to this blood bank
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT dn.donation_id, donor.blood_group, dn.units, dn.donation_date
            FROM donations dn
            INNER JOIN donors donor ON donor.donor_id = dn.donor_id
            WHERE dn.donation_id = %s
            AND dn.blood_bank_id = %s
            AND dn.status = 'Completed'
            AND NOT EXISTS (SELECT 1 FROM blood_units bu WHERE bu.donation_id = dn.donation_id)
            """,
            (donation_id, blood_bank_id)
        )

        donation = cursor.fetchone()

        if not donation:
            return jsonify({
                "success": False,
                "message": "Donation not found or donation is not completed."
            }), 400

        if blood_group != donation["blood_group"] or units != int(donation["units"]):
            return jsonify({"success": False, "message": "Blood group and quantity must match the selected completed donation."}), 400
        if expiry_date < str(donation["donation_date"]):
            return jsonify({"success": False, "message": "Expiry date cannot be before collection date."}), 400


        # -------------------------------------------------
        # Insert Blood Unit
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO blood_units
            (
                unit_id,
                blood_bank_id,
                donation_id,
                blood_group,
                collection_date,
                expiry_date,
                status,
                units
            )
            SELECT
                %s,
                %s,
                %s,
                donor.blood_group,
                dn.donation_date,
                %s,
                'Available',
                %s
            FROM donations dn
            INNER JOIN donors donor ON donor.donor_id = dn.donor_id
            WHERE dn.donation_id = %s
            AND dn.blood_bank_id = %s
            AND dn.status = 'Completed'
            AND NOT EXISTS (SELECT 1 FROM blood_units bu WHERE bu.donation_id = dn.donation_id)
            """,
            (
                unit_id,
                blood_bank_id,
                donation_id,
                expiry_date,
                units,
                donation_id,
                blood_bank_id
            )
        )

        if cursor.rowcount == 0:
            db.rollback()

            return jsonify({
                "success": False,
                "message": "Blood unit could not be created."
            }), 400


        db.commit()

        return jsonify({
            "success": True,
            "message": "Blood unit added successfully."
        })

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        cursor.close()
        db.close()


@bloodbank.route("/bloodbank/allocate", methods=["POST"])
def allocate_blood():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please login first."}), 401
    request_id = request.form.get("request_id", "").strip()
    unit_id = request.form.get("unit_id", "").strip()
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        staff = get_staff_and_bank(cursor)
        if not staff or not staff.get("blood_bank_id"):
            return jsonify({"success": False, "message": "Blood Bank staff profile not found."}), 403
        bank_id = staff["blood_bank_id"]
        cursor.execute("SELECT * FROM blood_requests WHERE request_id=%s AND status IN ('Pending','Approved') FOR UPDATE", (request_id,))
        blood_request = cursor.fetchone()
        cursor.execute("""SELECT bu.* FROM blood_units bu WHERE bu.unit_id=%s AND bu.blood_bank_id=%s
                       AND bu.status='Available' AND bu.expiry_date>=CURDATE() FOR UPDATE""", (unit_id, bank_id))
        unit = cursor.fetchone()
        if not blood_request or not unit:
            db.rollback()
            return jsonify({"success": False, "message": "Request or available unit not found."}), 400
        cursor.execute("SELECT is_compatible FROM compatibility WHERE recipient_blood_group=%s AND donor_blood_group=%s", (blood_request["blood_group"], unit["blood_group"]))
        match = cursor.fetchone()
        if not match or not match["is_compatible"]:
            db.rollback()
            return jsonify({"success": False, "message": "Selected blood group is not compatible."}), 400
        if int(unit["units"]) != int(blood_request["units_required"]):
            db.rollback()
            return jsonify({"success": False, "message": "Selected unit quantity must exactly match the request."}), 400
        allocation_id = "ALC" + uuid.uuid4().hex[:17].upper()
        cursor.execute("INSERT INTO allocation (allocation_id,request_id,unit_id,blood_bank_id,allocation_date,status) VALUES (%s,%s,%s,%s,CURDATE(),'Completed')", (allocation_id, request_id, unit_id, bank_id))
        cursor.execute("UPDATE blood_units SET status='Used' WHERE unit_id=%s AND status='Available'", (unit_id,))
        if cursor.rowcount != 1:
            db.rollback()
            return jsonify({"success": False, "message": "Blood unit is no longer available."}), 409
        cursor.execute("UPDATE blood_requests SET status='Fulfilled' WHERE request_id=%s", (request_id,))
        db.commit()
        return jsonify({"success": True, "message": "Allocation completed.", "allocation_id": allocation_id})
    except Exception as exc:
        db.rollback()
        return jsonify({"success": False, "message": str(exc)}), 500
    finally:
        cursor.close()
        db.close()
