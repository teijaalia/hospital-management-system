// On page load, verify user is doctor
document.addEventListener("DOMContentLoaded", async () => {
    const userType = localStorage.getItem("user_type");
    const userId = localStorage.getItem("user_id");
    const token = localStorage.getItem("token");

    if (!token || userType !== "doctor") {
        alert("Not authorized!");
        window.location.href = "index.html";
        return;
    }

    try {
        // Fetch doctor info
        const res = await fetch(`http://localhost:5000/doctor/${userId}`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const data = await res.json();

        document.getElementById("welcomeText").textContent =
            `Welcome Dr. ${data.First_Name} ${data.Last_Name}`;

    } catch (err) {
        console.error(err);
        alert("Error loading doctor data.");
    }
});

// Example navigation function
function goTo(page) {
    alert("This would open page: " + page);
}