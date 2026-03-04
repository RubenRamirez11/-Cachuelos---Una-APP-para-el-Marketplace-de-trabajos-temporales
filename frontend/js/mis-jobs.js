document.addEventListener("DOMContentLoaded", async function () {

    const token = localStorage.getItem("access_token");

    if (!token) {
        window.location.href = "login.html";
        return;
    }

    const container = document.getElementById("jobs-list");
    container.innerHTML = "<p>Cargando trabajos...</p>";

    try {

        const response = await fetch("http://127.0.0.1:8000/mis-jobs", {
            method: "GET",
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.log("Error del servidor:", errorText);
            container.innerHTML = "<p>No tienes permiso para ver esta página.</p>";
            return;
        }

        const data = await response.json();
        const jobs = data.jobs;

        if (!jobs || jobs.length === 0) {
            container.innerHTML = "<p>No has publicado trabajos aún.</p>";
            return;
        }

        container.innerHTML = "";

        jobs.forEach(job => {

            const div = document.createElement("div");
            div.classList.add("job-card");

            div.innerHTML = `
                <h3>${job.titulo}</h3>
                <p><strong>Pago:</strong> ${job.pago ?? "No especificado"}</p>
                <p><strong>Ubicación:</strong> ${job.ubicacion}</p>
                <p><strong>Estado:</strong> ${job.estado}</p>
                <p><strong>Fecha de creación:</strong> ${job.fecha_creacion}</p>
                <button onclick="verPostulantes(${job.job_id})">
                    Ver postulantes
                </button>
                <hr>
            `;

            container.appendChild(div);
        });

    } catch (error) {
        console.error("Error de conexión:", error);
        container.innerHTML = "<p>Error de conexión con el servidor.</p>";
    }

});

function verPostulantes(job_id) {
    window.location.href = `postulantes.html?job_id=${job_id}`;
}