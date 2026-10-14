// ==========================================
// BloodLink Donor Dashboard JavaScript
// ==========================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("BloodLink Donor Dashboard Loaded");

    // ============================
    // Elements
    // ============================

    const menuItems = document.querySelectorAll(".menu li");

    const profileLink = document.getElementById("profile-link");
    const profileSection = document.getElementById("profile-section");
    const backDashboard = document.getElementById("back-dashboard");

    const donateLink = document.getElementById("donate-link");
    const donateSection = document.getElementById("donate-section");
    const backFromDonate = document.getElementById("back-from-donate");
    const settingsLink = document.getElementById("settings-link");
    const settingsSection = document.getElementById("settings-section");
    const backFromSettings = document.getElementById("back-from-settings");
    const dashboardSections = document.querySelectorAll(
        ".welcome, .cards, .dashboard-grid"
    );

    const topbar = document.querySelector(".topbar");


    // ============================
    // Show Dashboard
    // ============================

    function showDashboard() {

        dashboardSections.forEach(section => {
            section.style.display = "";
        });

        if (profileSection) {
            profileSection.style.display = "none";
        }

        if (donateSection) {
            donateSection.style.display = "none";
        }
        if (settingsSection) {
            settingsSection.style.display = "none";
        }
        if (topbar) {
            topbar.style.display = "";
        }
    }


    // ============================
    // Show Profile
    // ============================

    if (profileLink && profileSection) {

        profileLink.addEventListener("click", function (e) {

            e.preventDefault();

            dashboardSections.forEach(section => {
                section.style.display = "none";
            });

            if (donateSection) {
                donateSection.style.display = "none";
            }

            profileSection.style.display = "block";

            if (topbar) {
                topbar.style.display = "";
            }

        });

    }


    // ============================
    // Back From Profile
    // ============================

    if (backDashboard) {

        backDashboard.addEventListener("click", function () {

            showDashboard();

        });

    }


    // ============================
    // Show Donate Blood
    // ============================

    if (donateLink && donateSection) {

        donateLink.addEventListener("click", function (e) {

            e.preventDefault();

            dashboardSections.forEach(section => {
                section.style.display = "none";
            });

            if (profileSection) {
                profileSection.style.display = "none";
            }

            donateSection.style.display = "block";

            if (topbar) {
                topbar.style.display = "";
            }

        });

    }


    // ============================
    // Back From Donate Blood
    // ============================

    if (backFromDonate) {

        backFromDonate.addEventListener("click", function () {

            showDashboard();

        });

    }
    // ============================
// Show Settings
// ============================

    if (settingsLink && settingsSection) {

        settingsLink.addEventListener("click", function (e) {

            e.preventDefault();

            dashboardSections.forEach(section => {
                section.style.display = "none";
            });

            if (profileSection) {
                profileSection.style.display = "none";
            }

            if (donateSection) {
                donateSection.style.display = "none";
            }

            settingsSection.style.display = "block";

            if (topbar) {
                topbar.style.display = "";
            }

        });

    }


// ============================
// Back From Settings
// ============================

    if (backFromSettings) {

         backFromSettings.addEventListener("click", function () {

             showDashboard();

        });

    }

    // ============================
    // Sidebar Active Menu
    // ============================

    menuItems.forEach(item => {

        item.addEventListener("click", function () {

            menuItems.forEach(i => {
                i.classList.remove("active");
            });

            this.classList.add("active");

        });

    });


    // ============================
    // Notification Button
    // ============================

    const notificationBtn = document.querySelector(".icon-btn");

    if (notificationBtn) {

        notificationBtn.addEventListener("click", function () {

            alert("🔔 No new notifications.");

        });

    }


    // ============================
    // Search Box
    // ============================

    const searchInput = document.querySelector(".search-box input");

    if (searchInput) {

        searchInput.addEventListener("keyup", function () {

            console.log("Searching :", this.value);

        });

    }


    // ============================
    // Card Hover Animation
    // ============================

    const cards = document.querySelectorAll(".card-box");

    cards.forEach(card => {

        card.addEventListener("mouseenter", () => {

            card.style.transition = ".3s";

        });

    });


    // ============================
    // Welcome Animation
    // ============================

    const welcome = document.querySelector(".welcome");

    if (welcome) {

        welcome.style.opacity = "0";
        welcome.style.transform = "translateY(20px)";

        setTimeout(() => {

            welcome.style.transition = ".7s";
            welcome.style.opacity = "1";
            welcome.style.transform = "translateY(0px)";

        }, 200);

    }


    // ============================
    // Footer Year
    // ============================

    const footer = document.querySelector("footer");

    if (footer) {

        const year = new Date().getFullYear();

        footer.innerHTML =
            `BloodLink © ${year} | Saving Lives Together ❤️`;

    }

});