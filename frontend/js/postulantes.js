document.addEventListener("DOMContentLoaded", async function () {

    const token = localStorage.getItem("access_token");

    if (!token) {
        window.location.href = "login.html";
        return;
    }

    const params = new URLSearchParams(window.location.search);
    const job_id = params.get("job_id");

    if (!job_id) {
        alert("Job no especificado");
        return;
    }

    const container = document.getElementById("postulantes-list");
    container.innerHTML = "<p>Cargando postulantes...</p>";

    try {

        const response = await fetch(
            `http://127.0.0.1:8000/jobs/${job_id}/postulaciones`,
            {
                headers: {
                    "Authorization": "Bearer " + token
                }
            }
        );

        if (!response.ok) {
            container.innerHTML = "<p>No tienes permiso o el job no existe.</p>";
            return;
        }

        const data = await response.json();
        const postulaciones = data.postulaciones;

        if (!postulaciones || postulaciones.length === 0) {
            container.innerHTML = "<p>No hay postulaciones aún.</p>";
            return;
        }

        container.innerHTML = "";

        postulaciones.forEach(p => {

            const div = document.createElement("div");

            div.innerHTML = `
                <h3>${p.nombre}</h3>
                <p><strong>Nacionalidad:</strong> ${p.nacionalidad}</p>
                <p><strong>Mensaje:</strong> ${p.mensaje}</p>
                <p><strong>Fecha:</strong> ${p.fecha_postulacion}</p>
                <p><strong>Estado:</strong> ${p.estado}</p>

                ${p.estado === "pendiente" ? `
                    <button onclick="aceptarPostulacion(${p.postulacion_id})">
                        Aceptar
                    </button>
                ` : ""}

                <hr>
            `;

            container.appendChild(div);
        });

    } catch (error) {
        console.error(error);
        container.innerHTML = "<p>Error de conexión.</p>";
    }

});


async function aceptarPostulacion(postulacion_id) {

    const token = localStorage.getItem("access_token");

    const confirmar = confirm("¿Seguro que deseas aceptar esta postulación? Se rechazarán las demás y se cerrará el trabajo.");

    if (!confirmar) return;

    try {

        const response = await fetch(
            `http://127.0.0.1:8000/postulaciones/${postulacion_id}/aceptar`,
            {
                method: "PATCH",
                headers: {
                    "Authorization": "Bearer " + token
                }
            }
        );

        const data = await response.json();

        if (response.ok) {
            alert("Postulación aceptada correctamente.");
            location.reload();
        } else {
            alert(data.detail || data.error || "No se pudo aceptar la postulación");
        }

    } catch (error) {
        alert("Error de conexión con el servidor");
    }
}