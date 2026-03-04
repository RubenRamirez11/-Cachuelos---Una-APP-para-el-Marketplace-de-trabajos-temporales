document.addEventListener("DOMContentLoaded", async function () {
    
    const token = localStorage.getItem("access_token");

    if (!token) {
        window.location.href = "login.html";
        return;
    }

    const container = document.getElementById("applications-list");
    container.innerHTML = "<p>Cargando postulaciones...</p>";

    try {

        const response = await fetch("http://127.0.0.1:8000/mis-postulaciones", {
            method: "GET",
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.log("Error del servidor:", errorText);
            container.innerHTML = "<p>Error al obtener postulaciones.</p>";
            return;
        }

        const data = await response.json();
        const applications = data.postulaciones;

        if (applications.length === 0) {
            container.innerHTML = "<p>No tienes postulaciones aún.</p>";
            return;
        }

        container.innerHTML = "";
        
        applications.forEach(app => {
            const div = document.createElement("div");
            div.classList.add("application-card");

            div.innerHTML = `
                <h4>${app.job?.titulo || "Sin título"}</h4>
                <p><strong>Estado del trabajo:</strong> ${app.job?.estado || "Desconocido"}</p>
                <p><strong>Mensaje enviado:</strong> ${app.mensaje || "Sin mensaje"}</p>
                <p><strong>Fecha de postulación:</strong> ${app.fecha_postulacion}</p>
                <hr>
            `;

            container.appendChild(div);
        });

    } catch (error) {
        console.error("Error de conexión:", error);
        container.innerHTML = "<p>Error de conexión con el servidor.</p>";
    }

});

