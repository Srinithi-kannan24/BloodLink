/* =========================================================
   BLOODLINK - BLOOD BANK DASHBOARD
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
   BLOOD INVENTORY FILTER
========================================================= */

function filterInventory() {

    const filter =
        document.getElementById("bloodGroupFilter").value;

    const table =
        document.getElementById("inventoryTable");

    if (!table) {
        return;
    }

    const rows =
        table.querySelectorAll("tbody tr");


    rows.forEach(function(row) {

        if (!row.cells.length) {
            return;
        }

        const bloodGroup =
            row.cells[0].innerText.trim();


        if (filter === "all" || bloodGroup === filter) {

            row.style.display = "";

        } else {

            row.style.display = "none";

        }

    });

}


/* =========================================================
   ADD BLOOD UNIT MODAL
========================================================= */

function openAddUnitModal() {

    const modal =
        document.getElementById("addUnitModal");

    if (modal) {

        modal.classList.add("show");

    }

}


function closeAddUnitModal() {

    const modal =
        document.getElementById("addUnitModal");

    if (modal) {

        modal.classList.remove("show");

    }

}


/* =========================================================
   ADD BLOOD UNIT
========================================================= */

async function addBloodUnit(event) {

    event.preventDefault();


    const bloodGroup =
        document.getElementById("newBloodGroup").value;

    const units =
        document.getElementById("newUnits").value;

    const expiryDate =
        document.getElementById("newExpiryDate").value;
    const donationId = document.getElementById("newDonationId").value;


    if (!bloodGroup || !units || !expiryDate || !donationId) {

        alert("Please fill all fields.");

        return;

    }


    const data = new FormData();
    data.append("blood_group", bloodGroup);
    data.append("units", units);
    data.append("expiry_date", expiryDate);
    data.append("donation_id", donationId);
    const response = await fetch("/bloodbank/add-unit", { method: "POST", body: data });
    const result = await response.json();
    alert(result.message || "Request failed.");
    if (response.ok && result.success) window.location.reload();

}

async function allocateRequest(event, requestId) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    data.append("request_id", requestId);
    const response = await fetch("/bloodbank/allocate", { method: "POST", body: data });
    const result = await response.json();
    alert(result.message || "Allocation failed.");
    if (response.ok && result.success) window.location.reload();
    return false;
}


/* =========================================================
   CLOSE MODAL WHEN CLICKING OUTSIDE
========================================================= */

window.addEventListener("click", function(event) {

    const modal =
        document.getElementById("addUnitModal");

    if (event.target === modal) {

        closeAddUnitModal();

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
