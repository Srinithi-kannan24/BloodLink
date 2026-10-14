/* =========================================================
   BLOODLINK - ADMIN DASHBOARD
========================================================= */


/* =========================================================
   SECTION NAVIGATION
========================================================= */

function showSection(sectionName, clickedButton = null) {

    const sections =
        document.querySelectorAll(".page-section");


    sections.forEach(function(section) {

        section.classList.remove("active-section");

    });


    const selectedSection =
        document.getElementById(sectionName);


    if (selectedSection) {

        selectedSection.classList.add("active-section");

    }


    const navItems =
        document.querySelectorAll(".nav-item");


    navItems.forEach(function(item) {

        item.classList.remove("active");

    });


    if (clickedButton) {

        clickedButton.classList.add("active");

    }


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });

}


/* =========================================================
   USER ROLE FILTER
========================================================= */

function filterUsers() {

    const filter =
        document.getElementById("roleFilter").value;


    const table =
        document.getElementById("usersTable");


    if (!table) {
        return;
    }


    const rows =
        table.querySelectorAll("tbody tr");


    rows.forEach(function(row) {

        const role =
            row.cells[3].getAttribute("data-role");


        if (
            filter === "all" ||
            role === filter
        ) {

            row.style.display = "";

        } else {

            row.style.display = "none";

        }

    });

}


/* =========================================================
   USER STATUS
========================================================= */

async function toggleUserStatus(button) {
    const row = button.closest("tr");
    const badge = row && row.querySelector(".status-badge");
    if (!row || !badge) return;
    const status = badge.innerText.trim() === "Active" ? "Inactive" : "Active";
    const data = new FormData();
    data.append("status", status);
    try {
        const response = await fetch(`/admin/users/${encodeURIComponent(row.dataset.userId)}/status`, { method: "POST", body: data });
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error(result.message || "Unable to update status.");
        window.location.reload();
    } catch (error) {
        alert(error.message || "Unable to update user status.");
    }
}


/* =========================================================
   ADD USER MODAL
========================================================= */

function openAddUserModal() {

    const modal =
        document.getElementById("addUserModal");


    if (modal) {

        modal.classList.add("show");

    }

}


function closeAddUserModal() {

    const modal =
        document.getElementById("addUserModal");


    if (modal) {

        modal.classList.remove("show");

    }

}


/* =========================================================
   ADD USER
========================================================= */

async function addUser(event) {

    event.preventDefault();


    const name =
        document.getElementById("newUserName").value;

    const email =
        document.getElementById("newUserEmail").value;

    const role =
        document.getElementById("newUserRole").value;

    const phone =
        document.getElementById("newUserPhone").value;
    const password = document.getElementById("newUserPassword").value;


    if (!name || !email || !role || !password) {

        alert("Please fill all required fields.");

        return;

    }


    const data = new FormData();
    data.append("full_name", name);
    data.append("email", email);
    data.append("password", password);
    data.append("role", role);
    data.append("phone", phone);
    data.append("hospital_id", document.getElementById("newUserHospital").value);
    data.append("blood_bank_id", document.getElementById("newUserBloodBank").value);
    data.append("blood_group", document.getElementById("newDonorBloodGroup").value);
    data.append("gender", document.getElementById("newDonorGender").value);
    data.append("date_of_birth", document.getElementById("newDonorDob").value);
    data.append("weight_kg", document.getElementById("newDonorWeight").value);
    data.append("city", document.getElementById("newDonorCity").value);
    data.append("district", document.getElementById("newDonorDistrict").value);
    try {
        const response = await fetch("/admin/users", { method: "POST", body: data });
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error(result.message || "Unable to create user.");
        alert(result.message);
        window.location.reload();
    } catch (error) {
        alert(error.message || "Unable to create user.");
    }

}


/* =========================================================
   EDIT PROFILE
========================================================= */

function openEditProfileModal() {

    const modal =
        document.getElementById("editProfileModal");


    if (modal) {

        modal.classList.add("show");

    }

}


function closeEditProfileModal() {

    const modal =
        document.getElementById("editProfileModal");


    if (modal) {

        modal.classList.remove("show");

    }

}


/* =========================================================
   SAVE PROFILE
========================================================= */

async function saveProfile(event) {

    event.preventDefault();


    const name =
        document.getElementById("profileName").value;

    const email =
        document.getElementById("profileEmail").value;

    const phone =
        document.getElementById("profilePhone").value;


    if (!name || !email) {

        alert("Name and email are required.");

        return;

    }


    const data = new FormData();
    data.append("name", name);
    data.append("email", email);
    data.append("phone", phone);
    try {
        const response = await fetch("/admin/profile", { method: "POST", body: data });
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error(result.message || "Unable to update profile.");
        alert(result.message);
        window.location.reload();
    } catch (error) {
        alert(error.message || "Unable to update profile.");
    }

}

function updateNewUserRoleFields() {
    const role = document.getElementById("newUserRole");
    if (!role) return;
    const groups = {
        HospitalStaff: ["hospitalRoleField"],
        BloodBankStaff: ["bloodBankRoleField"],
        Donor: ["donorRoleFields"]
    };
    ["hospitalRoleField", "bloodBankRoleField", "donorRoleFields"].forEach(id => {
        const field = document.getElementById(id);
        if (field) field.style.display = "none";
    });
    (groups[role.value] || []).forEach(id => {
        const field = document.getElementById(id);
        if (field) field.style.display = "block";
    });
    const requiredByRole = {
        newUserHospital: role.value === "HospitalStaff",
        newUserBloodBank: role.value === "BloodBankStaff",
        newDonorBloodGroup: role.value === "Donor",
        newDonorGender: role.value === "Donor",
        newDonorDob: role.value === "Donor",
        newDonorWeight: role.value === "Donor",
        newDonorCity: role.value === "Donor",
        newDonorDistrict: role.value === "Donor"
    };
    Object.entries(requiredByRole).forEach(([id, required]) => {
        const field = document.getElementById(id);
        if (field) field.required = required;
    });
}


/* =========================================================
   CLOSE MODALS WHEN CLICKING OUTSIDE
========================================================= */

window.addEventListener("click", function(event) {

    const addUserModal =
        document.getElementById("addUserModal");


    const profileModal =
        document.getElementById("editProfileModal");


    if (event.target === addUserModal) {

        closeAddUserModal();

    }


    if (event.target === profileModal) {

        closeEditProfileModal();

    }

});


/* =========================================================
   GLOBAL SEARCH
========================================================= */

document.addEventListener("DOMContentLoaded", function() {

    const roleSelect = document.getElementById("newUserRole");
    if (roleSelect) {
        roleSelect.addEventListener("change", updateNewUserRoleFields);
        updateNewUserRoleFields();
    }

    const searchInput =
        document.getElementById("globalSearch");


    if (!searchInput) {
        return;
    }


    searchInput.addEventListener("input", function() {

        const searchValue =
            searchInput.value.toLowerCase().trim();


        const activeSection =
            document.querySelector(
                ".page-section.active-section"
            );


        if (!activeSection) {
            return;
        }


        const rows =
            activeSection.querySelectorAll("tbody tr");


        rows.forEach(function(row) {

            const rowText =
                row.innerText.toLowerCase();


            if (
                rowText.includes(searchValue)
            ) {

                row.style.display = "";

            } else {

                row.style.display = "none";

            }

        });

    });

});
