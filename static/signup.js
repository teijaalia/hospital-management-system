document.getElementById("signupForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    const first_name = document.getElementById("first_name").value;
    const last_name = document.getElementById("last_name").value;
    const address = document.getElementById("address").value;
    const phone = document.getElementById("phone").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch("http://127.0.0.1:5000/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                first_name,
                last_name,
                address,
                phone,
                email,
                password
            })
        });

        const data = await response.json();

        if (data.status === "ok") {
            alert("Account created successfully!");
            window.location.href = "/";
        } else {
            alert(data.message || "Signup failed");
        }
    } catch (err) {
        alert("Backend not reachable.");
        console.error(err);
    }
});