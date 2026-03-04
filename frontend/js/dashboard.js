document.addEventListener("DOMContentLoaded", async function () {

    const token = localStorage.getItem("access_token");

    if (!token) {
        window.location.href = "login.html";
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/me", {
            method: "GET",
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (!response.ok) {
            localStorage.removeItem("access_token");
            window.location.href = "login.html";
            return;
        }

        const user = await response.json();

        document.getElementById("welcome").innerText =
            "Bienvenido, " + user.nombre;

        const content = document.getElementById("content");

        // 🔥 CAMBIO IMPORTANTE AQUÍ
        if (user.rol === "empleador") {

            content.innerHTML = `
                <h3>Panel de Empleador</h3>

                <div style="margin-top: 15px;">
                    <button 
                        onclick="window.location.href='mis-jobs.html'"
                        style="padding: 10px 15px; cursor: pointer;">
                        Ver mis trabajos
                    </button>
                </div>

                <div style="margin-top: 15px;">
                    <button 
                        onclick="window.location.href='crear-job.html'"
                        style="padding: 10px 15px; cursor: pointer;">
                        Crear nuevo trabajo
                    </button>
                </div>
            `;
        } else {

            content.innerHTML = `
                <h3>Panel de Trabajador</h3>
                <div style="margin-top: 15px;">
                    <button onclick="window.location.href='mis-postulaciones.html'"
                        style="padding: 10px 15px; cursor: pointer;">
                        Ver mis postulaciones
                    </button>
                </div>

                <hr style="margin:20px 0;">

                <h3>Trabajos disponibles</h3>
                <div id="jobs-container"></div>
            `;

            // 🔥 Cargar trabajos automáticamente
            loadJobs();
        }

    } catch (error) {
        console.log(error);
    }

});

async function getMisPostulaciones() {

    const token = localStorage.getItem("access_token");

    try {

        const response = await fetch("http://127.0.0.1:8000/mis-postulaciones", {
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (!response.ok) {
            return new Set();
        }

        const data = await response.json();

        const jobIds = new Set();

        data.postulaciones.forEach(p => {
            jobIds.add(p.job.job_id);
        });

        return jobIds;

    } catch (error) {
        console.log("Error obteniendo postulaciones:", error);
        return new Set();
    }
}

async function loadJobs() {

    const container = document.getElementById("jobs-container");

    try {

        const response = await fetch("http://127.0.0.1:8000/jobs");

        if (!response.ok) {
            container.innerHTML = "<p>Error al cargar trabajos.</p>";
            return;
        }

        const data = await response.json();
        const jobs = data.jobs;

        if (!jobs || jobs.length === 0) {
            container.innerHTML = "<p>No hay trabajos disponibles.</p>";
            return;
        }

        // 🔥 Obtener mis postulaciones
        const misPostulaciones = await getMisPostulaciones();

        container.innerHTML = "";

        jobs.forEach(job => {

            const jobCard = document.createElement("div");
            jobCard.style.border = "1px solid black";
            jobCard.style.padding = "10px";
            jobCard.style.marginBottom = "10px";

            let botonHTML;

            if (misPostulaciones.has(job.job_id)) {
                botonHTML = `<button disabled>Ya postulaste</button>`;
            } else {
                botonHTML = `<button onclick="postular(${job.job_id})">Postular</button>`;
            }

            jobCard.innerHTML = `
                <h4>${job.titulo}</h4>
                <p>${job.descripcion || ""}</p>
                <p><strong>Pago:</strong> ${job.pago}</p>
                <p><strong>Ubicación:</strong> ${job.ubicacion}</p>
                ${botonHTML}
            `;

            container.appendChild(jobCard);
        });

    } catch (error) {
        console.log("ERROR:", error);
        container.innerHTML = "<p>Error de conexión con el servidor.</p>";
    }
}

// 🔥 Función postular
async function postular(jobId) {

    const token = localStorage.getItem("access_token");

    if (!token) {
        alert("Debes iniciar sesión.");
        window.location.href = "login.html";
        return;
    }

    const mensaje = prompt("Escribe un mensaje para el empleador (opcional):");

    // 🔥 Si presiona Cancelar, NO enviar postulación
    if (mensaje === null) {
        return;
    }

    try {

        const response = await fetch("http://127.0.0.1:8000/postulaciones", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },
            body: JSON.stringify({
                job_id: jobId,
                mensaje: mensaje.trim() === "" ? null : mensaje
            })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.detail || data.error || "Error al postular.");
            return;
        }

        alert("✅ Postulación enviada correctamente");

    } catch (error) {
        console.log(error);
        alert("Error de conexión con el servidor.");
    }
}

function logout() {
    localStorage.removeItem("access_token");
    window.location.href = "login.html";
}

