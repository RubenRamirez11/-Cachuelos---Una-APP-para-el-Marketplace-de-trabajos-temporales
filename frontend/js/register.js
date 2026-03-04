document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("register-form");
    const messageDiv = document.getElementById("message");

    form.addEventListener("submit", async function (event) {

        event.preventDefault();

        const nombre = document.getElementById("nombre").value;
        const nacionalidad = document.getElementById("nacionalidad").value;
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;
        const rol = document.getElementById("rol").value;

        messageDiv.innerHTML = "Creando usuario...";

        try {

            const response = await fetch("http://127.0.0.1:8000/auth/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    nombre,
                    nacionalidad,
                    email,
                    password,
                    rol
                })
            });

            const data = await response.json();

            if (!response.ok || data.error) {
                messageDiv.innerHTML = `<div style="color:red;">
                    ${data.error || "Error al registrar usuario"}
                </div>`;
                return;
            }

            messageDiv.innerHTML = `
                <div style="color:green;">
                    ✅ Usuario creado correctamente.
                    Redirigiendo a login...
                </div>
            `;

            setTimeout(() => {
                window.location.href = "login.html";
            }, 1500);

        } catch (error) {
            messageDiv.innerHTML = `
                <div style="color:red;">
                    Error de conexión con el servidor
                </div>
            `;
        }

    });

});