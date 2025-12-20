// Liitetään login-funktio form-submittiin
document.getElementById("loginForm").addEventListener("submit", async function(e) {
    e.preventDefault(); // estää form submitin reloadin

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch("http://127.0.0.1:5000/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (data.status === "ok") {
            localStorage.setItem("userName", data.name);

            if (data.type.toLowerCase() === "patient") {
                window.location.href = "patient.html";
            } else if (data.type.toLowerCase() === "doctor") {
                window.location.href = "doctor.html";
            } else if (data.type.toLowerCase() === "admin") {
                window.location.href = "administrator.html";
            }
        } else {
            alert("Wrong credentials");
        }
    } catch (err) {
        alert("Could not connect to backend. Make sure app.py is running.");
        console.error(err);
    }
});
