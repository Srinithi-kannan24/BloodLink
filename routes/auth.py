from flask import Blueprint, render_template, request, redirect, url_for

auth_bp = Blueprint("auth", __name__)

# Login Page
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        role = request.form.get("role")

        # Temporary routing (will be replaced with MySQL later)
        if role == "Donor":
            return redirect(url_for("auth.donor_dashboard"))

        elif role == "Hospital":
            return redirect(url_for("auth.hospital_dashboard"))

        elif role == "Blood Bank":
            return redirect(url_for("auth.bloodbank_dashboard"))

        elif role == "Admin":
            return redirect(url_for("auth.admin_dashboard"))

    return render_template("login.html")


# Temporary Dashboards

@auth_bp.route("/donor")
def donor_dashboard():
    return "<h1>Donor Dashboard</h1>"


@auth_bp.route("/hospital")
def hospital_dashboard():
    return "<h1>Hospital Dashboard</h1>"


@auth_bp.route("/bloodbank")
def bloodbank_dashboard():
    return "<h1>Blood Bank Dashboard</h1>"


@auth_bp.route("/admin")
def admin_dashboard():
    return "<h1>Admin Dashboard</h1>"