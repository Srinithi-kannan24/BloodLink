// ================================
// Elements
// ================================

const roleSelect = document.getElementById("role");
const dynamicFields = document.getElementById("dynamic-fields");

const password = document.getElementById("password");
const confirmPassword = document.getElementById("confirmPassword");

const togglePassword = document.getElementById("togglePassword");
const toggleConfirmPassword = document.getElementById("toggleConfirmPassword");

// ================================
// Password Toggle
// ================================

togglePassword.addEventListener("click", () => {

    const type = password.type === "password" ? "text" : "password";
    password.type = type;

    togglePassword.classList.toggle("bi-eye");
    togglePassword.classList.toggle("bi-eye-slash");

});

toggleConfirmPassword.addEventListener("click", () => {

    const type = confirmPassword.type === "password" ? "text" : "password";
    confirmPassword.type = type;

    toggleConfirmPassword.classList.toggle("bi-eye");
    toggleConfirmPassword.classList.toggle("bi-eye-slash");

});

// ================================
// Dynamic Fields
// ================================

roleSelect.addEventListener("change", function () {

    const role = this.value;

    if (role === "Donor") {

        dynamicFields.innerHTML = `

            <div class="role-section">

                <div class="mb-3">

                    <label class="form-label">Blood Group</label>

                    <select class="form-select auth-select" name="blood_group" required>

                        <option value="">Select Blood Group</option>

                        <option>A+</option>
                        <option>A-</option>
                        <option>B+</option>
                        <option>B-</option>
                        <option>AB+</option>
                        <option>AB-</option>
                        <option>O+</option>
                        <option>O-</option>

                    </select>

                </div>

                <div class="mb-3">

                    <label class="form-label">Date of Birth</label>

                    <input type="date"
                           class="form-control auth-input"
                           name="date_of_birth"
                           required>

                </div>

                <div class="mb-3">

                    <label class="form-label">Gender</label>

                    <select class="form-select auth-select"
                            name="gender"
                            required>

                        <option value="">Select Gender</option>
                        <option>Male</option>
                        <option>Female</option>
                        <option>Other</option>

                    </select>

                </div>

                <div class="mb-3">

                    <label class="form-label">Weight (kg)</label>

                    <input type="number"
                           class="form-control auth-input"
                           name="weight_kg"
                           placeholder="Enter weight"
                           required>

                </div>

                <div class="mb-3">

    <label class="form-label">City</label>

    <input type="text"
           class="form-control auth-input"
           name="city"
           placeholder="Enter City"
           required>

</div>

<div class="mb-3">

    <label class="form-label">District</label>

    <input type="text"
           class="form-control auth-input"
           name="district"
           placeholder="Enter District"
           required>

</div>
            </div>

        `;

    }

    else if (role === "Hospital") {

        dynamicFields.innerHTML = `

            <div class="role-section">

                <div class="mb-3">

                    <label class="form-label">
                        Hospital License Number
                    </label>

                    <input type="text"
                           class="form-control auth-input"
                           name="license"
                           placeholder="Enter License Number"
                           required>

                </div>

                <div class="mb-3">

                    <label class="form-label">
                        Address
                    </label>

                    <textarea class="form-control auth-textarea"
                              name="address"
                              placeholder="Enter Address"
                              required></textarea>

                </div>

            </div>

        `;

    }

    else if (role === "Blood Bank") {

        dynamicFields.innerHTML = `

            <div class="role-section">

                <div class="mb-3">

                    <label class="form-label">
                        Blood Bank License Number
                    </label>

                    <input type="text"
                           class="form-control auth-input"
                           name="license"
                           placeholder="Enter License Number"
                           required>

                </div>

                <div class="mb-3">

                    <label class="form-label">
                        Storage Capacity
                    </label>

                    <input type="number"
                           class="form-control auth-input"
                           name="capacity"
                           placeholder="Units"
                           required>

                </div>

                <div class="mb-3">

                    <label class="form-label">
                        Address
                    </label>

                    <textarea class="form-control auth-textarea"
                              name="address"
                              placeholder="Enter Address"
                              required></textarea>

                </div>

            </div>

        `;

    }

    else {

        dynamicFields.innerHTML = `

            <div class="empty-role-message">

                Select a role to continue.

            </div>

        `;

    }

});

// ================================
// Password Validation
// ================================

document.querySelector(".auth-form").addEventListener("submit", function (e) {

    if (password.value !== confirmPassword.value) {

        e.preventDefault();

        alert("Passwords do not match!");

        return;

    }

});