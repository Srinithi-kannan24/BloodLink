/* =========================================================
   BLOODLINK - HOSPITAL DASHBOARD
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
   NEW BLOOD REQUEST MODAL
========================================================= */

function openRequestModal() {

    const modal =
        document.getElementById("requestModal");

    if (modal) {

        modal.classList.add("show");

    }

}


function closeRequestModal() {

    const modal =
        document.getElementById("requestModal");

    if (modal) {

        modal.classList.remove("show");

    }

}


/* =========================================================
   SUBMIT BLOOD REQUEST
========================================================= */

function submitBloodRequest(event) {

    event.preventDefault();


    const bloodGroup =
        document.getElementById("requestBloodGroup").value;

    const units =
        document.getElementById("requestUnits").value;

    let priority =
        document.getElementById("requestPriority").value;

    const requiredDate =
        document.getElementById("requiredDate").value;

    if (priority === "Normal") priority = "Routine";

    if (
        !bloodGroup ||
        !units ||
        !priority ||
        !requiredDate
    ) {

        alert("Please fill all required fields.");

        return;

    }


    const data = new FormData();
    data.append("blood_group", bloodGroup);
    data.append("units", units);
    data.append("urgency", priority);
    data.append("required_date", requiredDate);
    fetch("/hospital/request", { method: "POST", body: data })
        .then(response => response.json().then(body => ({ response, body })))
        .then(({ response, body }) => {
            alert(body.message || "Request failed.");
            if (response.ok && body.success) window.location.reload();
        })
        .catch(() => alert("Unable to submit request. Please try again."));

}


/* =========================================================
   EDIT PROFILE MODAL
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

function saveProfile(event) {

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
    fetch("/hospital/profile", { method: "POST", body: data })
        .then(response => response.json().then(body => ({ response, body })))
        .then(({ response, body }) => {
            alert(body.message || "Profile update failed.");
            if (response.ok && body.success) window.location.reload();
        })
        .catch(() => alert("Unable to save profile. Please try again."));

}


/* =========================================================
   CLOSE MODALS WHEN CLICKING OUTSIDE
========================================================= */

window.addEventListener("click", function(event) {

    const requestModal =
        document.getElementById("requestModal");

    const profileModal =
        document.getElementById("editProfileModal");


    if (event.target === requestModal) {

        closeRequestModal();

    }


    if (event.target === profileModal) {

        closeEditProfileModal();

    }

});


/* =========================================================
   GLOBAL SEARCH
========================================================= */

document.addEventListener("DOMContentLoaded", function() {

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


            if (rowText.includes(searchValue)) {

                row.style.display = "";

            } else {

                row.style.display = "none";

            }

        });

    });

});
