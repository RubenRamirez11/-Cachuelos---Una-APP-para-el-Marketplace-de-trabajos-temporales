// Esperar a que el DOM cargue completamente
document.addEventListener("DOMContentLoaded", function () {

    const token = localStorage.getItem("access_token");

    const form = document.getElementById("login-form");
    const messageDiv = document.getElementById("message");

    // ==============================
    // 🔐 LÓGICA DE LOGIN (solo si existe el form)
    // ==============================
    if (form) {

        form.addEventListener("submit", async function (event) {

            event.preventDefault();

            const email = document.getElementById("email").value;
            const password = document.getElementById("password").value;

            messageDiv.innerHTML = "Cargando...";

            try {
                const response = await fetch("http://127.0.0.1:8000/auth/login", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                });

                const data = await response.json();
                console.log("RESPUESTA LOGIN:", data);

                if (!response.ok) {
                    messageDiv.innerHTML = `<div class="error">${data.detail || "Error al iniciar sesión"}</div>`;
                    return;
                }

                // Guardar token
                localStorage.setItem("access_token", data.access_token);

                messageDiv.innerHTML = `<div class="success">Login exitoso</div>`;

                setTimeout(() => {
                    window.location.href = "dashboard.html";
                }, 1000);

            } catch (error) {
                messageDiv.innerHTML = `<div class="error">No se pudo conectar al servidor</div>`;
            }

        });

    } else {
        // ==============================
        // 🔒 PROTEGER PÁGINAS PRIVADAS
        // ==============================

        if (!token) {
            window.location.href = "login.html";
        }
    }

});


// ==============================
// 🚪 LOGOUT GLOBAL
// ==============================
function logout() {
    localStorage.removeItem("access_token");
    window.location.href = "login.html";
}