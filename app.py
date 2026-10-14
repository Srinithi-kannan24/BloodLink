from flask import Flask

from routes.home import home_bp
from routes.auth import auth_bp
from routes.donor import donor_bp
from routes.bloodbank import bloodbank
from routes.hospital import hospital
from routes.admin import admin

app = Flask(__name__)
app.secret_key = "bloodlink-secret-key"
# Register Blueprints
app.register_blueprint(home_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(donor_bp)
app.register_blueprint(bloodbank)
app.register_blueprint(hospital)
app.register_blueprint(admin)


if __name__ == "__main__":
    app.run(debug=True)